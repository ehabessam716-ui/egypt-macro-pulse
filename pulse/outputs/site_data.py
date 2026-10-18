"""Data bundle for the web app (site/): data/pulse-data.js, data/manifest.js, data/series/<id>.js.

Files are JavaScript (not JSON) so the app also works when opened straight from disk (file://):
each file calls a global callback, which a <script> tag can load without a web server.
"""
from __future__ import annotations

import json
import math
import shutil
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .. import calendar as cal
from ..core import BRIEFS, ROOT, SITE, is_business_day, load_yaml, now_cairo, today_cairo
from ..data import DataView, catalog
from ..events import active_events, review_queue
from ..indices import compute
from ..outputs.brief import GLOSSARY
from . import fmt

WEB = Path(__file__).resolve().parents[1] / "web"

DOMAINS = [
    ("fx", "The pound", "الجنيه", ["fx_cbe_official", "fx_market", "fx_gold_implied", "gold_gap_pct", "fx_chg_20d", "fx_chg_3m",
                                    "fx_vol_20d", "fx_market_gap_pct", "tbill_3m_yield", "tbill_12m_yield", "tbill_12m_btc",
                                    "tbill_12m_accepted_ratio", "carry_ex_post_3m", "fx_parallel", "eurobond_yield", "cds_5y"]),
    ("monetary", "Rates & inflation", "الفايدة والتضخم",
     ["cbe_odr", "cbe_olr", "cbe_mainop", "interbank_overnight", "real_headline", "real_core", "real_expected",
      "cpi_urban_yoy", "cpi_core_yoy", "cpi_urban_mom", "cpi_core_mom", "cpi_fv_yoy", "cpi_regulated_yoy",
      "cpi_national_yoy", "infl_expectations", "infl_target", "cbe_mpc_tone"]),
    ("external", "Money in & out", "الفلوس الداخلة والخارجة",
     ["nir", "nir_chg_3m", "nir_months_imports", "remittances", "remittances_yoy", "remittances_ytd", "remittances_12m_sum",
      "bop_ca_fy", "bop_overall_fy", "trade_balance_fy", "imports_oil_fy", "imports_nonoil_fy", "tourism_receipts_fy",
      "suez_receipts_fy", "fdi_net_fy", "portfolio_net_fy", "suez_ratio_7dma", "suez_transits", "tourism_arrivals_ytd",
      "suez_revenue_fy"]),
    ("fiscal", "Debt & IMF", "الديون وصندوق النقد",
     ["ext_debt_stock", "ext_debt_gdp", "ext_debt_service_actual", "debt_service_next_year_to_nir", "budget_oil_assumption",
      "imf_weo_gdp", "imf_weo_cpi", "imf_weo_ca", "imf_weo_debt", "gov_debt_gdp", "interest_to_revenue"]),
    ("energy", "Energy & gold", "البترول والدهب",
     ["brent", "brent_fut", "brent_gap", "ca_pressure_pct_gdp", "brent_egp", "brent_egp_qavg_chg", "wti", "ttf_fut", "ttf",
      "henry_hub", "wheat", "fuel_92", "fuel_95", "fuel_diesel", "gold_eg_21k", "gold_eg_24k", "gold_eg_pound", "xauusd",
      "xauusd_spot", "gold_local_premium_pct", "xagusd"]),
    ("real", "Growth", "النمو",
     ["pmi", "pmi_3m_avg", "pmi_implied_gdp", "gdp_growth", "gdp_growth_fy", "wb_gdp_growth", "lng_imports", "unemployment"]),
    ("global", "World & US", "العالم وأمريكا",
     ["fed_funds", "us10y", "us2y", "breakeven10y", "us_cpi_yoy", "us_core_cpi_yoy", "us_unemp", "dxy", "usd_broad", "vix",
      "em_spread_proxy", "msci_em_proxy", "eurusd", "euro_area_hicp", "saudi_pmi", "uae_pmi"]),
    ("geo", "Region & risk", "المنطقة والمخاطر",
     ["gpr_daily", "gpr_global", "gpr_threats", "gpr_acts", "gpr_egypt", "gpr_israel", "gpr_saudi", "hormuz_ratio_7dma",
      "babelmandeb_ratio_7dma", "hormuz_transits", "gdelt_egypt_economy_tone", "gdelt_egypt_economy_vol"]),
    ("health", "Healthcare", "الدوا والصحة", ["eda_signal", "cpi_health_yoy", "cpi_med_products_yoy", "fx_cbe_official"]),
]

# +1 = a rise is pressure on the pound (red), -1 = a rise is relief (blue). Others stay neutral.
DIRECTION = {
    "fx_cbe_official": 1, "fx_market": 1, "fx_gold_implied": 1, "gold_gap_pct": 1, "fx_chg_20d": 1, "fx_chg_3m": 1,
    "fx_vol_20d": 1, "fx_market_gap_pct": 1, "fx_parallel": 1, "cds_5y": 1, "eurobond_yield": 1,
    "real_headline": -1, "real_core": -1, "real_expected": -1, "cpi_urban_yoy": 1, "cpi_core_yoy": 1,
    "cpi_urban_mom": 1, "cpi_core_mom": 1, "nir": -1, "nir_chg_3m": -1, "nir_months_imports": -1, "remittances": -1,
    "remittances_yoy": -1, "remittances_12m_sum": -1, "bop_ca_fy": -1, "tourism_receipts_fy": -1,
    "suez_receipts_fy": -1, "fdi_net_fy": -1, "portfolio_net_fy": -1, "suez_ratio_7dma": -1, "brent": 1, "brent_fut": 1,
    "brent_gap": 1, "ca_pressure_pct_gdp": 1, "brent_egp": 1, "brent_egp_qavg_chg": 1, "ttf_fut": 1, "ttf": 1, "wheat": 1,
    "vix": 1, "dxy": 1, "usd_broad": 1, "us10y": 1, "em_spread_proxy": 1, "gpr_daily": 1, "gpr_egypt": 1,
    "hormuz_ratio_7dma": -1, "babelmandeb_ratio_7dma": -1, "debt_service_next_year_to_nir": 1, "ext_debt_stock": 1,
    "tbill_12m_yield": 1, "tbill_12m_btc": -1, "tbill_12m_accepted_ratio": -1, "pmi": -1, "gold_local_premium_pct": 1,
}

KEY_HISTORY = ["fx_cbe_official", "fx_market", "fx_gold_implied", "real_headline", "real_core", "real_expected", "nir",
               "brent", "brent_fut", "budget_oil_assumption", "suez_ratio_7dma", "babelmandeb_ratio_7dma",
               "hormuz_ratio_7dma", "remittances", "remittances_12m_sum", "gpr_daily", "pmi", "cpi_urban_yoy",
               "cpi_core_yoy", "cbe_odr"]

CONCEPTS = {
    "hidden peg": ("When reserves fall while the official rate doesn't move, the central bank is probably defending the rate. "
                   "It can hold for a while, then the rate jumps.",
                   "لما الاحتياطي يقل والسعر الرسمي ثابت، غالبا البنك المركزي بيسند السعر، وده ممكن يستمر فترة وبعدين السعر يتحرك مرة واحدة."),
    "parallel market premium": ("The gap between a free-market price of dollars (gold, parallel) and the official rate shows "
                                "how much people doubt the official price.",
                                "الفرق بين سعر الدولار برة البنوك أو في الدهب والسعر الرسمي بيبين الناس مصدقة السعر الرسمي قد إيه."),
    "real interest rate / carry": ("Interest minus inflation. A high real rate pays foreign investors to hold pounds "
                                   "(carry trade), which brings dollars in.",
                                   "الفايدة ناقص التضخم. لما تكون عالية، المستثمر الأجنبي بيكسب لو مسك جنيه، فبيدخل دولارات."),
    "pass-through": ("A weaker pound makes imports dearer, which lifts consumer prices 1–6 months later.",
                     "ضعف الجنيه بيغلي الحاجات المستوردة، والأسعار بتزيد بعد شهر لستة شهور."),
    "oil shock channels": ("Expensive oil hits Egypt three ways: the fuel-subsidy bill (budget), the import bill "
                           "(dollars) and, later, pump prices (inflation).",
                           "البترول الغالي بيأثر على مصر بتلات طرق: دعم الوقود في الموازنة، وفاتورة الاستيراد بالدولار، وبعدين أسعار البنزين."),
    "current account deficit": ("More money leaves through trade and income than comes in. It must be financed by "
                                "investment or borrowing, or the currency weakens.",
                                "فلوس خارجة من التجارة والدخل أكتر من الداخلة، ولازم تتغطى باستثمار أو قروض وإلا الجنيه يضعف."),
    "IMF as guarantor": ("An active IMF programme reassures investors that financing and reforms continue.",
                         "وجود برنامج مع صندوق النقد بيطمن المستثمرين إن التمويل والإصلاحات مستمرة."),
    "credit ratings (lag markets)": ("Rating agencies usually confirm what bond markets already priced in.",
                                     "وكالات التصنيف غالبا بتأكد اللي السوق عمله قبلها."),
    "deferred pass-through": ("Frozen fuel prices postpone the inflation hit; they don't cancel it.",
                              "تثبيت أسعار الوقود بيأجل أثر التضخم، مش بيلغيه."),
    "chokepoints": ("Suez, Bab el-Mandeb and Hormuz carry Egypt's canal income and much of the world's oil.",
                    "قناة السويس وباب المندب وهرمز فيهم دخل القناة وجزء كبير من بترول العالم."),
    "Suez Canal / chokepoints": ("Fewer ships through Suez means fewer dollars from canal fees.",
                                 "سفن أقل في القناة يعني دولارات أقل من رسوم المرور."),
    "remittances": ("Money Egyptians abroad send home — Egypt's largest single source of dollars.",
                    "الفلوس اللي المصريين في الخارج بيبعتوها، وهي أكبر مصدر للدولار في مصر."),
    "reserve adequacy": ("Reserves measured in months of imports: below about 3–5 months is thin.",
                         "الاحتياطي بيتقاس بعدد شهور الواردات اللي يغطيها، وأقل من تلات لخمس شهور يعتبر قليل."),
    "inflation vs growth trade-off": ("High rates fight inflation but slow the economy; a weak PMI makes that choice harder.",
                                      "الفايدة العالية بتحارب التضخم بس بتبطأ الاقتصاد، وضعف النشاط بيصعب القرار."),
}

_ICONS = {"fx": "£", "monetary": "%", "external": "⇄", "fiscal": "🏛", "energy": "⛽", "real": "📈", "global": "🌐",
          "geo": "🧭", "health": "✚"}


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def _points(s: pd.Series, since: pd.Timestamp | None = None, max_points: int | None = None) -> list:
    if since is not None:
        s = s[s.index >= since]
    if max_points and len(s) > max_points:
        s = s.iloc[-max_points:]
    return [[d.strftime("%Y-%m-%d"), round(float(v), 6)] for d, v in s.items()]


def series_payload(v: DataView, sid: str, today: date) -> dict:
    m = catalog()[sid]
    o = v.latest(sid)
    p = {"id": sid, "name_en": m["name_en"], "name_ar": m["name_ar"], "domain": m["domain"], "unit": m.get("unit") or "",
         "freq": m["frequency"], "access": m["access"], "definition": m.get("definition_note"),
         "sign": DIRECTION.get(sid, 0), "source_key": m.get("source")}
    if o is None:
        p["empty"] = True
        return p
    prev = v.nth_latest(sid, 1)
    s = v.series(sid)
    cal_name = m.get("calendar", "all")
    p.update(value=_clean(o.value), display=fmt(o.value, m.get("unit")), date=o.date.isoformat(), source=o.source_name,
             url=o.source_url if o.source_url.startswith("http") else None, quality=o.quality, stale=o.stale,
             conflict=o.conflict, note=o.note, release=o.release_date, obs_time=o.obs_time, n=len(s),
             closed=bool(m["frequency"] == "daily" and cal_name != "all" and not is_business_day(today, cal_name) and o.date < today),
             spark=_points(s, max_points=60))
    if prev is not None:
        p.update(prev=_clean(prev.value), prev_date=prev.date.isoformat(), change=_clean(o.value - prev.value),
                 change_pct=_clean((o.value / prev.value - 1) * 100) if prev.value else None)
    return p


def _rules(conn, as_of: date) -> list[dict]:
    rows = conn.execute("SELECT * FROM rule_hits WHERE run_date=? ORDER BY fired DESC, strength DESC", (as_of.isoformat(),)).fetchall()
    cfg = load_yaml("rules.yaml")["rules"]
    out = []
    for r in rows:
        info = json.loads(r["inputs_json"])
        c = cfg.get(r["rule_id"], {})
        concept = r["concept_tag"]
        out.append({"id": r["rule_id"], "name": info.get("name"), "fired": bool(r["fired"]), "evaluable": bool(r["evaluable"]),
                    "direction": r["direction"], "strength": round(r["strength"] or 0, 2), "en": r["explanation_en"],
                    "ar": r["explanation_ar"], "concept": concept, "learn": CONCEPTS.get(concept), "domain": c.get("domain"),
                    "affects": info.get("affects", []), "inputs": info.get("inputs", []), "missing": info.get("missing", []),
                    "lag": c.get("lag_note"), "params": c.get("params", {})})
    return out


def next_runs(now) -> list[dict]:
    """Upcoming scheduled jobs (mirrors scripts/install_schedule.py)."""
    sched = [("daily", {6, 0, 1, 2, 3}, "09:30"), ("daily", {6, 0, 1, 2, 3}, "18:30"), ("global", {0, 1, 2, 3, 4}, "23:30"),
             ("weekly", {3}, "20:00"), ("gpr", {0}, "12:00"), ("calendar", set(range(7)), "07:00")]
    out = []
    for k in range(0, 8):
        d = (now + timedelta(days=k)).date()
        for job, days, hm in sched:
            if d.weekday() in days:
                h, mi = map(int, hm.split(":"))
                t = now.replace(year=d.year, month=d.month, day=d.day, hour=h, minute=mi, second=0, microsecond=0)
                if t > now:
                    out.append({"job": job, "at": t.isoformat()})
    return sorted(out, key=lambda x: x["at"])[:6]


def build_bundle(conn) -> dict:
    as_of = today_cairo()
    now = now_cairo()
    v = DataView(conn, as_of)
    idx = compute(conn, as_of)
    series = {sid: series_payload(v, sid, as_of) for sid in catalog()}
    hist_since = pd.Timestamp(as_of - timedelta(days=365 * 3 + 30))
    history = {sid: _points(v.series(sid), since=hist_since if catalog()[sid]["frequency"] == "daily" else None)
               for sid in KEY_HISTORY}
    ppi_hist = [dict(r) for r in conn.execute(
        "SELECT run_date, value, coverage_pct, kind FROM index_values WHERE index_id='PPI' ORDER BY run_date").fetchall()]
    sub_hist = {}
    for r in conn.execute("SELECT run_date, index_id, value FROM index_values WHERE index_id LIKE 'PPI_%' AND kind='backtest' ORDER BY run_date"):
        sub_hist.setdefault(r["index_id"][4:], []).append([r["run_date"], r["value"]])
    brief_md = (BRIEFS / f"{as_of.isoformat()}.md")
    briefs = sorted([p.stem for p in BRIEFS.glob("*.md")], reverse=True)[:30]
    cov = {"fresh": 0, "stale": 0, "very_stale": 0, "missing": 0, "manual_missing": 0}
    for sid, p in series.items():
        if p.get("empty"):
            cov["missing"] += 1
            if p["access"] in ("MANUAL", "PAID"):
                cov["manual_missing"] += 1
        else:
            cov[["fresh", "stale", "very_stale"][p["stale"]]] += 1
    sources = [dict(r) for r in conn.execute(
        """SELECT source, status, MAX(finished_at) AS at, rows_added AS rows, error FROM fetch_log f WHERE finished_at =
           (SELECT MAX(finished_at) FROM fetch_log g WHERE g.source=f.source) GROUP BY source ORDER BY source""").fetchall()]
    for s in sources:
        s["error"] = (s["error"] or "").splitlines()[0][:200] if s["error"] else None
    domains = [{"id": d, "name_en": en, "name_ar": ar, "icon": _ICONS[d], "series": [s for s in ids if s in catalog()]}
               for d, en, ar, ids in DOMAINS]
    version = conn.execute("SELECT COALESCE(MAX(retrieved_at),'') || '|' || COUNT(*) FROM observations").fetchone()[0]
    return {
        "version": f"{version}|{now.isoformat(timespec='minutes')}",
        "generated": now.isoformat(timespec="seconds"), "as_of": as_of.isoformat(),
        "market": {"egypt_open": is_business_day(as_of, "egypt"), "global_open": is_business_day(as_of, "global")},
        "ppi": {**idx["ppi"], "history": ppi_hist},
        "subindices": [{"id": k, **{kk: vv for kk, vv in s.items() if kk != "components"},
                        "components": s["components"], "history": sub_hist.get(k, [])} for k, s in idx["subindices"].items()],
        "extra": [{"id": k, **s} for k, s in idx["extra"].items()],
        "domains": domains, "series": series, "history": history, "rules": _rules(conn, as_of),
        "events": active_events(conn, as_of, include_tags=True), "queue": review_queue(conn, 40),
        "calendar": cal.upcoming(conn, 21), "sources": sources, "coverage": {**cov, "total": len(series)},
        "glossary": [{"ar": a, "en": e, "explain": x} for a, e, x in GLOSSARY],
        "brief": {"date": as_of.isoformat(), "md": brief_md.read_text(encoding="utf-8") if brief_md.exists() else None,
                  "archive": briefs},
        "next_runs": next_runs(now),
    }


def _js(callback: str, payload) -> str:
    return f"{callback}({json.dumps(payload, ensure_ascii=False, default=str, separators=(',', ':'))});\n"


def write_site(conn) -> str:
    SITE.mkdir(parents=True, exist_ok=True)
    data_dir = SITE / "data"
    (data_dir / "series").mkdir(parents=True, exist_ok=True)
    # static app files
    for f in WEB.iterdir():
        if f.is_file():
            shutil.copy2(f, SITE / f.name)
    plotly_js = SITE / "plotly.min.js"
    if not plotly_js.exists():
        from plotly.offline import get_plotlyjs
        plotly_js.write_text(get_plotlyjs(), encoding="utf-8")
    # briefs travel with the site (so they open on GitHub Pages too)
    bdir = SITE / "briefs"
    bdir.mkdir(exist_ok=True)
    for f in sorted(BRIEFS.glob("*.*"))[-60:]:
        if f.suffix in (".md", ".html"):
            shutil.copy2(f, bdir / f.name)
    bundle = build_bundle(conn)
    (data_dir / "pulse-data.js").write_text(_js("window.__pulseData", bundle), encoding="utf-8")
    v = DataView(conn)
    for sid in catalog():
        s = v.series(sid, include_future=True)
        f = v.frame(sid, include_future=True)
        rows = [[d.isoformat(), round(float(val), 6), src, (url if str(url).startswith("http") else None), q]
                for d, val, src, url, q in zip(f["obs_date"], f["value"], f["source_name"], f["source_url"], f["quality_flag"])] if not f.empty else []
        (data_dir / "series" / f"{sid}.js").write_text(_js("window.__pulseSeries", {"id": sid, "rows": rows}), encoding="utf-8")
    # manifest last: the app polls it and reloads the bundle when the version changes
    (data_dir / "manifest.js").write_text(_js("window.__pulseManifest", {"version": bundle["version"],
                                                                          "generated": bundle["generated"]}), encoding="utf-8")
    return str(SITE / "index.html")
