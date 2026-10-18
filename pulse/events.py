"""Events: taxonomy, decay, auto-candidates from news, and the 2-outlet promotion rule.

score(t) = severity × direction × 0.5^((t − event_date)/half_life_days); dropped below 0.1 or after expires_at.
Only 'confirmed' and 'reported' events count. 'candidate' events sit in the review queue.
A candidate becomes 'reported' only when >= 2 independent outlets from the RSS list report it within 48 h.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta, timezone

from .core import get_logger, load_yaml, utc_now_iso

log = get_logger("pulse.events")

# Outlets that count as independent corroboration (SPEC §3.10 RSS list, those that work).
INDEPENDENT_OUTLETS = {"Daily News Egypt", "Egypt Independent", "Mada Masr", "EnterpriseAM", "Central Bank of Egypt"}
PROMOTION_WINDOW_H = 48
LOOKBACK_DAYS = 10

TYPE_AR = {
    "regional_war_escalation": "تصعيد حرب في المنطقة", "chokepoint_disruption": "تعطيل في ممرات الملاحة",
    "ceasefire_or_deescalation": "وقف إطلاق نار أو تهدئة", "domestic_unrest": "اضطرابات داخلية",
    "cabinet_change": "تغيير وزاري", "imf_staff_level_agreement": "اتفاق على مستوى الخبراء مع صندوق النقد",
    "imf_board_approval_disbursement": "موافقة صندوق النقد وصرف شريحة", "imf_review_delay": "تأجيل مراجعة صندوق النقد",
    "rating_upgrade": "رفع التصنيف الائتماني", "rating_downgrade": "خفض التصنيف الائتماني",
    "rating_affirmation": "تثبيت التصنيف الائتماني", "gulf_deposit_or_megadeal": "ودائع أو صفقة خليجية كبيرة",
    "privatization_ipo_proceeds": "حصيلة طروحات وبيع حصص", "eurobond_issuance_success": "إصدار سندات دولية ناجح",
    "eurobond_maturity_due": "استحقاق سندات دولية قريب", "fuel_price_hike": "زيادة أسعار الوقود",
    "fuel_price_freeze": "تثبيت أسعار الوقود", "load_shedding_start": "رجوع تخفيف الأحمال",
    "lng_supply_disruption": "تعطل إمدادات الغاز", "eu_mfa_tranche": "شريحة دعم من الاتحاد الأوروبي",
    "sanctions_on_partner_or_shipping": "عقوبات على شركاء أو على الشحن", "eda_repricing_decision": "قرار تسعير من هيئة الدواء",
}


def taxonomy() -> dict:
    return load_yaml("events_taxonomy.yaml")


def sync_types(conn) -> None:
    for t, d in taxonomy()["event_types"].items():
        conn.execute("""INSERT INTO event_types VALUES (?,?,?,?,?,?) ON CONFLICT(event_type) DO UPDATE SET
                        default_severity=excluded.default_severity, default_direction=excluded.default_direction,
                        default_half_life_days=excluded.default_half_life_days, affects_subindex=excluded.affects_subindex,
                        description=excluded.description""",
                     (t, d["severity"], d["direction"], d["half_life_days"], d["subindex"], d["description"]))


def event_id(event_date: date, event_type: str, key: str) -> str:
    return hashlib.sha1(f"{event_date}|{event_type}|{key}".encode()).hexdigest()[:16]


def upsert_event(conn, *, event_date: date, event_type: str, title_en: str, title_ar: str, confidence: str,
                 source_name: str, source_url: str, entered_by: str, notes: str | None = None,
                 severity: int | None = None, direction: int | None = None, half_life_days: float | None = None,
                 key: str | None = None) -> str:
    types = taxonomy()["event_types"]
    if event_type not in types:
        raise ValueError(f"unknown event_type {event_type!r}")
    d = types[event_type]
    sev = severity or d["severity"]
    dirn = d["direction"] if direction is None else direction
    hl = half_life_days or d["half_life_days"]
    expires = event_date + timedelta(days=int(hl * 5))
    eid = event_id(event_date, event_type, key or source_url)
    now = utc_now_iso()
    conn.execute("""INSERT INTO events(event_id,event_date,event_type,domain,title_en,title_ar,severity,direction,
                    half_life_days,expires_at,confidence,source_name,source_url,entered_by,notes,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET
                    title_en=excluded.title_en, title_ar=excluded.title_ar, severity=excluded.severity,
                    direction=excluded.direction, half_life_days=excluded.half_life_days, expires_at=excluded.expires_at,
                    confidence=CASE WHEN events.confidence='confirmed' THEN 'confirmed' ELSE excluded.confidence END,
                    notes=excluded.notes, updated_at=excluded.updated_at""",
                 (eid, event_date.isoformat(), event_type, d["subindex"], title_en, title_ar or TYPE_AR.get(event_type, ""),
                  sev, dirn, hl, expires.isoformat(), confidence, source_name, source_url, entered_by, notes, now, now))
    return eid


def decayed(severity: float, direction: float, half_life: float, event_date: date, as_of: date) -> float:
    days = (as_of - event_date).days
    if days < 0:
        return 0.0
    return severity * direction * 0.5 ** (days / half_life)


def active_events(conn, as_of: date, include_tags: bool = False) -> list[dict]:
    drop = taxonomy().get("drop_below", 0.1)
    rows = conn.execute("""SELECT * FROM events WHERE confidence IN ('confirmed','reported') AND event_date<=?
                           ORDER BY event_date DESC""", (as_of.isoformat(),)).fetchall()
    out = []
    for r in rows:
        r = dict(r)
        if r["expires_at"] and as_of > date.fromisoformat(r["expires_at"]):
            continue
        ed = date.fromisoformat(r["event_date"])
        mag = decayed(r["severity"], 1, r["half_life_days"], ed, as_of)  # magnitude ignoring direction
        if mag < drop:
            continue
        r["score"] = round(decayed(r["severity"], r["direction"], r["half_life_days"], ed, as_of), 3)
        r["magnitude"] = round(mag, 3)
        r["weight_left"] = round(mag / r["severity"], 3)
        if r["direction"] == 0 and not include_tags:
            r["tag_only"] = True
        out.append(r)
    return out


def subindex_event_points(conn, as_of: date) -> dict[str, float]:
    tx = taxonomy()
    scale, cap = tx.get("index_points_per_unit", 8), tx.get("index_cap", 40)
    pts: dict[str, float] = {}
    for e in active_events(conn, as_of):
        pts[e["domain"]] = pts.get(e["domain"], 0.0) + e["score"] * scale
    return {k: max(-cap, min(cap, v)) for k, v in pts.items()}


def review_queue(conn, limit: int = 50) -> list[dict]:
    rows = conn.execute("""SELECT e.*, (SELECT COUNT(DISTINCT outlet) FROM event_sources s WHERE s.event_id=e.event_id) AS n_outlets
                           FROM events e WHERE confidence='candidate' ORDER BY event_date DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ candidates from news
def classify(text: str) -> list[str]:
    t = text.lower()
    hits = []
    for et, d in taxonomy()["event_types"].items():
        for kw in d.get("keywords", []):
            if re.search(kw, t):
                hits.append(et)
                break
    # an affirmation headline is not an upgrade/downgrade
    if "rating_affirmation" in hits:
        hits = [h for h in hits if h not in ("rating_upgrade", "rating_downgrade")]
    return hits


def _pub(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def scan_candidates(conn, now: datetime | None = None) -> dict:
    """Match recent news to event types, cluster per type within 48 h, apply the 2-outlet rule."""
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(days=LOOKBACK_DAYS)).isoformat()
    items = conn.execute("SELECT * FROM news_items WHERE published_at>=? ORDER BY published_at", (since,)).fetchall()
    stats = {"matched": 0, "new_candidates": 0, "promoted": 0, "corroborated_manual": 0}
    for it in items:
        types = classify(f"{it['title']} {it['summary'] or ''}"[:1500])
        conn.execute("UPDATE news_items SET matched_types=? WHERE url=?", (",".join(types), it["url"]))
        pub = _pub(it["published_at"])
        if not types or pub is None:
            continue
        stats["matched"] += 1
        for et in types:
            lo = (pub - timedelta(hours=PROMOTION_WINDOW_H)).date().isoformat()
            hi = (pub + timedelta(hours=PROMOTION_WINDOW_H)).date().isoformat()
            ev = conn.execute("""SELECT * FROM events WHERE event_type=? AND event_date BETWEEN ? AND ?
                                 ORDER BY CASE confidence WHEN 'confirmed' THEN 0 WHEN 'reported' THEN 1 ELSE 2 END
                                 LIMIT 1""", (et, lo, hi)).fetchone()
            if ev is None:
                eid = upsert_event(conn, event_date=pub.date(), event_type=et, title_en=it["title"][:300],
                                   title_ar=TYPE_AR.get(et, ""), confidence="candidate", source_name=it["outlet"],
                                   source_url=it["url"], entered_by="auto_candidate",
                                   notes="auto-proposed from news keywords; needs review", key=it["url"])
                stats["new_candidates"] += 1
            else:
                eid = ev["event_id"]
                if ev["entered_by"] == "manual":
                    stats["corroborated_manual"] += 1
            conn.execute("INSERT OR IGNORE INTO event_sources VALUES (?,?,?,?,?)",
                         (eid, it["outlet"], it["url"], it["title"][:300], it["published_at"]))
    # promotion: >= 2 independent outlets within 48 h of the first report
    for ev in conn.execute("SELECT event_id FROM events WHERE confidence='candidate'").fetchall():
        srcs = conn.execute("SELECT outlet, published_at FROM event_sources WHERE event_id=? ORDER BY published_at",
                            (ev["event_id"],)).fetchall()
        if should_promote([(s["outlet"], _pub(s["published_at"])) for s in srcs]):
            outlets = sorted({s["outlet"] for s in srcs if s["outlet"] in INDEPENDENT_OUTLETS})
            conn.execute("""UPDATE events SET confidence='reported', updated_at=?,
                            notes=COALESCE(notes,'') || ' | auto-promoted: reported by ' || ? WHERE event_id=?""",
                         (utc_now_iso(), ", ".join(outlets), ev["event_id"]))
            stats["promoted"] += 1
    log.info("event scan: %s", stats)
    return stats


def should_promote(reports: list[tuple[str, datetime | None]]) -> bool:
    rs = sorted([(o, t) for o, t in reports if t is not None and o in INDEPENDENT_OUTLETS], key=lambda x: x[1])
    for i, (o1, t1) in enumerate(rs):
        outlets = {o1}
        for o2, t2 in rs[i + 1:]:
            if t2 - t1 <= timedelta(hours=PROMOTION_WINDOW_H):
                outlets.add(o2)
        if len(outlets) >= 2:
            return True
    return False


def seed_events(conn) -> int:
    n = 0
    for e in load_yaml("seeds.yaml").get("events", []):
        d = e["event_date"] if isinstance(e["event_date"], date) else date.fromisoformat(str(e["event_date"]))
        upsert_event(conn, event_date=d, event_type=e["event_type"], title_en=e["title_en"], title_ar=e["title_ar"],
                     confidence=e["confidence"], source_name=e["source_name"], source_url=e["source_url"],
                     entered_by="manual", notes=e.get("notes"))
        n += 1
    return n


def set_confidence(conn, event_id: str, confidence: str) -> bool:
    if confidence not in ("confirmed", "reported", "candidate"):
        raise ValueError(confidence)
    cur = conn.execute("UPDATE events SET confidence=?, updated_at=? WHERE event_id=?", (confidence, utc_now_iso(), event_id))
    return cur.rowcount > 0
