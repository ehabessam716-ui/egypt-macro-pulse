"""data/manual/manual_inputs.xlsx — one tab per MANUAL series + an events tab.

The workbook is pre-filled with the spec's seed values. It is never required: an empty tab just
lowers coverage. Every row needs a date, a numeric value and a source URL or it is rejected.
"""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from .core import MANUAL_XLSX, REPORTS, get_logger, load_yaml
from .data import catalog
from .db import add_obs

log = get_logger("pulse.manual")
OBS_COLS = ["obs_date", "value", "unit", "source_name", "source_url", "source_date", "quality_flag", "note"]
EVENT_COLS = ["event_date", "event_type", "title_en", "title_ar", "severity", "direction", "half_life_days",
              "confidence", "source_name", "source_url", "notes"]
SEED_TAB = "seed_checks"  # seeds for series that also have an automatic source


def manual_series() -> list[str]:
    return [sid for sid, m in catalog().items() if m["access"] in ("MANUAL", "PAID")]


def _tab(sid: str) -> str:
    return sid[:31]


def build_frames() -> dict[str, pd.DataFrame]:
    seeds = load_yaml("seeds.yaml")
    frames: dict[str, list[dict]] = {_tab(s): [] for s in manual_series()}
    frames[SEED_TAB] = []
    manual = set(manual_series())
    for s in seeds.get("observations", []):
        row = {"obs_date": str(s["obs_date"]), "value": s["value"], "unit": s.get("unit"),
               "source_name": s["source_name"], "source_url": s["source_url"],
               "source_date": str(s.get("source_date") or ""), "quality_flag": "secondary", "note": s.get("note", "")}
        if s["series_id"] in manual:
            frames[_tab(s["series_id"])].append(row)
        else:
            frames[SEED_TAB].append({"series_id": s["series_id"], **row})
    out = {"README": pd.DataFrame({"how to use": [
        "One tab per MANUAL series. Add rows; never delete the header.",
        "Required per row: obs_date (YYYY-MM-DD), value (number), source_url (http...). Rows missing any are rejected.",
        "quality_flag: secondary (press/aggregator) or manual (you read the primary source).",
        "Monthly obs_date = 1st of month; fiscal year = 1 July of the start year; quarterly = 1st day of quarter.",
        "'events' tab: confidence must be confirmed or reported; event_type from config/events_taxonomy.yaml.",
        f"'{SEED_TAB}' holds spec seeds for series that are also collected automatically (official wins).",
        "Leaving this file empty is fine: missing data lowers the coverage %, it never stops a run.",
    ]})}
    for tab, rows in frames.items():
        cols = (["series_id"] + OBS_COLS) if tab == SEED_TAB else OBS_COLS
        out[tab] = pd.DataFrame(rows, columns=cols)
    ev = [{**{k: e.get(k, "") for k in EVENT_COLS}, "event_date": str(e["event_date"])} for e in seeds.get("events", [])]
    out["events"] = pd.DataFrame(ev, columns=EVENT_COLS)
    return out


def create_workbook(force: bool = False) -> str:
    """Create the workbook if missing. Existing files are kept (only missing tabs are added)."""
    MANUAL_XLSX.parent.mkdir(parents=True, exist_ok=True)
    frames = build_frames()
    if MANUAL_XLSX.exists() and not force:
        existing = pd.ExcelFile(MANUAL_XLSX).sheet_names
        missing = {k: v for k, v in frames.items() if k not in existing}
        if missing:
            with pd.ExcelWriter(MANUAL_XLSX, engine="openpyxl", mode="a") as w:
                for tab, df in missing.items():
                    df.to_excel(w, sheet_name=tab, index=False)
        return f"kept existing workbook; added {len(missing)} missing tab(s)"
    with pd.ExcelWriter(MANUAL_XLSX, engine="openpyxl") as w:
        order = ["README", "events", SEED_TAB] + [t for t in frames if t not in ("README", "events", SEED_TAB)]
        for tab in order:
            frames[tab].to_excel(w, sheet_name=tab, index=False)
            ws = w.sheets[tab]
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 18 if tab != "README" else 110
    return f"created {MANUAL_XLSX} with {len(frames)} tabs"


def _date(v) -> date | None:
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "NaT", "nan"):
        return None
    if isinstance(v, (datetime, pd.Timestamp)):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v).strip()[:10])
    except ValueError:
        return None


def import_workbook(conn) -> dict:
    from .events import upsert_event

    if not MANUAL_XLSX.exists():
        create_workbook()
    xl = pd.ExcelFile(MANUAL_XLSX)
    stats = {"rows": 0, "rejected": 0, "events": 0}
    rejects: list[str] = []
    cat = catalog()
    for tab in xl.sheet_names:
        if tab == "README":
            continue
        df = xl.parse(tab)
        if tab == "events":
            for i, r in df.iterrows():
                d = _date(r.get("event_date"))
                url = str(r.get("source_url") or "")
                if not d or not url.startswith("http") or not str(r.get("event_type") or "").strip():
                    if str(r.get("event_type") or "").strip() or d:
                        rejects.append(f"events row {i + 2}: needs event_date, event_type and source_url")
                        stats["rejected"] += 1
                    continue
                conf = str(r.get("confidence") or "reported").strip()
                if conf not in ("confirmed", "reported"):
                    rejects.append(f"events row {i + 2}: confidence must be confirmed/reported")
                    stats["rejected"] += 1
                    continue
                upsert_event(conn, event_date=d, event_type=str(r["event_type"]).strip(),
                             title_en=str(r.get("title_en") or ""), title_ar=str(r.get("title_ar") or ""),
                             confidence=conf, source_name=str(r.get("source_name") or ""), source_url=url,
                             entered_by="manual", notes=str(r.get("notes") or "") or None,
                             severity=_opt_int(r.get("severity")), direction=_opt_int(r.get("direction")),
                             half_life_days=_opt_float(r.get("half_life_days")))
                stats["events"] += 1
            continue
        for i, r in df.iterrows():
            sid = str(r.get("series_id") or "").strip() if tab == SEED_TAB else tab
            if sid not in cat:
                if sid:
                    rejects.append(f"{tab} row {i + 2}: unknown series_id {sid!r}")
                    stats["rejected"] += 1
                continue
            d = _date(r.get("obs_date"))
            val = pd.to_numeric(r.get("value"), errors="coerce")
            url = str(r.get("source_url") or "")
            if d is None and pd.isna(val) and not url.strip("nan"):
                continue  # empty row
            if d is None or pd.isna(val) or not url.startswith("http"):
                rejects.append(f"{tab} row {i + 2}: needs obs_date, numeric value and source_url")
                stats["rejected"] += 1
                continue
            q = str(r.get("quality_flag") or "secondary").strip()
            q = q if q in ("secondary", "manual", "official") else "secondary"
            note = r.get("note")
            add_obs(conn, sid, d, float(val), unit=str(r.get("unit") or cat[sid].get("unit") or ""),
                    source_name=str(r.get("source_name") or "manual input"), source_url=url, quality_flag=q,
                    release_date=_date(r.get("source_date")),
                    obs_note=(None if note is None or pd.isna(note) or not str(note).strip() else str(note)))
            stats["rows"] += 1
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "manual_import_rejects.md").write_text(
        "# Manual import — rejected rows\n\n" + ("\n".join(f"- {x}" for x in rejects) or "None.") + "\n",
        encoding="utf-8")
    log.info("manual import: %s", stats)
    return stats


def _opt_int(v):
    v = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(v) else int(v)


def _opt_float(v):
    v = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(v) else float(v)


def seed_verification(conn) -> str:
    """Compare every spec seed with the official/primary value for the same series & date (SPEC §11)."""
    seeds = load_yaml("seeds.yaml").get("observations", [])
    lines = ["# Seed verification — spec seeds vs primary sources", "",
             "Seeds stay in the DB as quality 'secondary'; when a primary value exists for the same date it wins.", "",
             "| series | obs date | seed | seed source | primary value | primary source | status |", "|---|---|---|---|---|---|---|"]
    counts = {"confirmed": 0, "differs": 0, "secondary only": 0}
    for s in seeds:
        od = str(s["obs_date"])
        row = conn.execute("""SELECT value, source_name FROM observations WHERE series_id=? AND obs_date=? AND
                              quality_flag IN ('official','unofficial') ORDER BY quality_flag='official' DESC, vintage DESC LIMIT 1""",
                           (s["series_id"], od)).fetchone()
        if row is None:
            status, pv, ps = "secondary only", "—", "—"
        else:
            pv, ps = row["value"], row["source_name"]
            status = "confirmed" if abs(pv - s["value"]) <= max(0.005 * abs(s["value"]), 0.051) else "differs"
        counts[status] += 1
        lines.append(f"| {s['series_id']} | {od} | {s['value']} | {s['source_name']} | {pv} | {ps} | **{status}** |")
    lines[2] += f"  Summary: {counts}."
    path = REPORTS / "seed_verification.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)
