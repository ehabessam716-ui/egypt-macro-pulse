"""`pulse doctor`: DB integrity, stale series, failed sources, missing manual inputs, brief/language checks."""
from __future__ import annotations

import re
from datetime import timedelta

from .core import BRIEFS, EXPORTS, MANUAL_XLSX, SITE, get_logger, load_yaml, today_cairo
from .data import DataView, catalog, sync_catalog

log = get_logger("pulse.doctor")


def doctor(conn, fix: bool = False, quiet: bool = False) -> dict:
    issues: list[tuple[str, str]] = []  # (level, message) level: critical / warn / info
    ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if ok != "ok":
        issues.append(("critical", f"SQLite integrity_check: {ok}"))
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        issues.append(("critical", f"foreign key problems: {len(fk)}"))
    # catalog in sync with config
    n_db = conn.execute("SELECT COUNT(*) FROM series_catalog").fetchone()[0]
    if n_db != len(catalog()):
        if fix:
            sync_catalog(conn)
            issues.append(("info", "series_catalog re-synced with config/series.yaml"))
        else:
            issues.append(("warn", f"series_catalog has {n_db} rows, config has {len(catalog())} (run with --fix)"))
    # observations referring to unknown series
    unknown = [r[0] for r in conn.execute("SELECT DISTINCT series_id FROM observations").fetchall() if r[0] not in catalog()]
    if unknown:
        issues.append(("warn", f"observations for series not in catalog: {', '.join(unknown)}"))
    # rows without source or with NULL value and no reason (schema forbids; check anyway)
    bad = conn.execute("SELECT COUNT(*) FROM observations WHERE source_url IS NULL OR source_url='' OR (value IS NULL AND null_reason IS NULL)").fetchone()[0]
    if bad:
        issues.append(("critical", f"{bad} observations without source or NULL reason"))
    # conflicts
    conf = conn.execute("SELECT DISTINCT series_id FROM observations WHERE conflict=1").fetchall()
    if conf:
        issues.append(("info", "sources disagree (>0.5%) on: " + ", ".join(r[0] for r in conf) + " — both kept, primary shown"))
    # stale + missing
    v = DataView(conn)
    stale, vstale, missing_auto, missing_manual = [], [], [], []
    for sid, m in catalog().items():
        o = v.latest(sid)
        if o is None:
            (missing_manual if m["access"] in ("MANUAL", "PAID") else missing_auto).append(sid)
        elif o.stale == 1:
            stale.append(f"{sid} ({o.date})")
        elif o.stale == 2:
            vstale.append(f"{sid} ({o.date})")
    if missing_auto:
        issues.append(("warn", f"automatic series with no data yet: {', '.join(missing_auto)}"))
    if vstale:
        issues.append(("warn", f"very stale (excluded from indices): {', '.join(vstale)}"))
    if stale:
        issues.append(("info", f"stale: {', '.join(stale)}"))
    if missing_manual:
        issues.append(("info", f"MANUAL series with no rows (lower coverage only): {len(missing_manual)} — {', '.join(missing_manual)}"))
    # failed sources in the last run of each collector
    rows = conn.execute("""SELECT source, status, error, finished_at FROM fetch_log f WHERE finished_at =
                           (SELECT MAX(finished_at) FROM fetch_log g WHERE g.source=f.source)""").fetchall()
    for r in rows:
        if r["status"] != "ok":
            issues.append(("warn", f"collector {r['source']} failed at {r['finished_at']}: {(r['error'] or '').splitlines()[0][:200]}"))
    never = sorted(set(_collectors()) - {r["source"] for r in rows})
    if never:
        issues.append(("info", f"collectors never run yet: {', '.join(never)}"))
    # manual workbook
    if not MANUAL_XLSX.exists():
        if fix:
            from .manual import create_workbook
            create_workbook()
            issues.append(("info", "manual_inputs.xlsx re-created"))
        else:
            issues.append(("warn", "data/manual/manual_inputs.xlsx missing (run with --fix)"))
    # outputs + Arabic rule
    today = today_cairo()
    brief = BRIEFS / f"{today.isoformat()}.md"
    if brief.exists():
        from .outputs.brief import body_of
        body = body_of(brief.read_text(encoding="utf-8"))
        if re.search(r"[A-Za-z]", body):
            issues.append(("critical", f"Latin letters found in the Arabic body of {brief.name}"))
        if "| المصطلح بالعربي | English term | شرح بسيط |" not in brief.read_text(encoding="utf-8"):
            issues.append(("critical", f"glossary table missing in {brief.name}"))
    else:
        issues.append(("info", f"no brief for today yet ({brief.name})"))
    for rid, r in load_yaml("rules.yaml")["rules"].items():
        if re.search(r"[A-Za-z]", re.sub(r"\{[^}]*\}", "", r.get("ar", ""))):
            issues.append(("critical", f"rules.yaml {rid}: Arabic template contains Latin letters"))
    if not (SITE / "index.html").exists():
        issues.append(("warn", "site/index.html not built yet"))
    if not (EXPORTS / "fact_observations.csv").exists():
        issues.append(("warn", "Power BI export not built yet"))
    # last successful run recency
    last = conn.execute("SELECT MAX(finished_at) FROM fetch_log WHERE status='ok'").fetchone()[0]
    if last and last[:10] < (today - timedelta(days=3)).isoformat():
        issues.append(("warn", f"no successful fetch since {last} — is the scheduler running?"))
    crit = [m for lvl, m in issues if lvl == "critical"]
    if not quiet:
        print(f"pulse doctor — {today}  ({len(crit)} critical, {sum(l == 'warn' for l, _ in issues)} warnings)")
        for lvl, m in issues:
            print(f"  [{lvl.upper():8}] {m}")
        if not issues:
            print("  all checks passed")
    conn.commit()
    return {"critical": crit, "issues": issues}


def _collectors() -> list[str]:
    from .collectors import JOBS
    return JOBS["all"]
