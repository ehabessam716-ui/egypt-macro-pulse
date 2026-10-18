"""Command line: `pulse run --job daily|global|weekly|gpr|calendar|all` and individual steps."""
from __future__ import annotations

import argparse
import sys
import time
import uuid

from .core import get_logger, now_cairo

log = get_logger("pulse")


def init(conn) -> None:
    from .data import sync_catalog
    from .events import sync_types
    from .manual import create_workbook, import_workbook

    sync_catalog(conn)
    sync_types(conn)
    log.info(create_workbook())
    import_workbook(conn)
    conn.commit()


def step(name: str, fn, *a, **kw):
    t0 = time.perf_counter()
    try:
        out = fn(*a, **kw)
        log.info("step %-10s ok (%.1fs)", name, time.perf_counter() - t0)
        return out
    except Exception as e:  # noqa: BLE001 — one failing step never stops the run
        log.exception("step %s FAILED: %s", name, e)
        return None


def run_job(job: str, backfill: bool = False, dry_run: bool = False) -> int:
    from . import calendar as cal
    from .collectors import JOBS, Ctx, run_collectors
    from .db import connect

    run_id = f"{now_cairo():%Y%m%d-%H%M%S}-{job}-{uuid.uuid4().hex[:4]}"
    log.info("=== run %s (job=%s%s) ===", run_id, job, ", DRY RUN" if dry_run else "")
    conn = connect()
    try:
        step("init", init, conn)
        if dry_run:
            log.info("dry run: would run collectors %s", JOBS.get(job))
            from .doctor import doctor
            return 0 if step("doctor", doctor, conn, quiet=True) is not None else 1
        results = run_collectors(conn, JOBS[job], Ctx(run_id=run_id, backfill=backfill))
        step("calendar", cal.refresh, conn)
        conn.commit()
        if job == "calendar":
            log.info("alerts written to %s", cal.write_alerts(conn))
            return 0
        from .events import scan_candidates
        step("events", scan_candidates, conn)
        conn.commit()
        analyse(conn, brief=job in ("daily", "all"), weekly=job in ("weekly", "all"), backtest=job in ("weekly", "all"))
        cal.write_alerts(conn)
        failed = [k for k, v in results.items() if v["status"] != "ok"]
        log.info("=== run %s done; collectors failed: %s ===", run_id, failed or "none")
        return 0
    finally:
        conn.commit()
        conn.close()


def analyse(conn, brief: bool = True, weekly: bool = False, backtest: bool = False) -> None:
    from .derive import compute_all
    from .export import export_powerbi
    from .indices import compute_indices, run_backtest
    from .outputs.brief import write_brief
    from .outputs.site_data import write_site
    from .outputs.weekly import write_weekly
    from .rules import evaluate_rules

    from . import calendar as cal
    step("calendar", cal.refresh, conn)
    step("derive", compute_all, conn)
    step("rules", evaluate_rules, conn)
    step("indices", compute_indices, conn)
    if backtest:
        step("backtest", run_backtest, conn)
    conn.commit()
    if brief:
        step("brief", write_brief, conn)
    if weekly:
        step("weekly", write_weekly, conn)
    step("site", write_site, conn)
    step("export", export_powerbi, conn)
    from .manual import seed_verification
    step("seeds", seed_verification, conn)
    conn.commit()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pulse", description="Egypt Macro Pulse — learning tool, not financial advice")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a scheduled job")
    r.add_argument("--job", default="daily", choices=["daily", "global", "weekly", "gpr", "calendar", "all"])
    r.add_argument("--backfill", action="store_true", help="re-download full history")
    r.add_argument("--dry-run", action="store_true", help="check setup without fetching")
    c = sub.add_parser("collect", help="run named collectors only")
    c.add_argument("names", nargs="+")
    c.add_argument("--backfill", action="store_true")
    sub.add_parser("init", help="create DB, catalog, manual workbook; import manual inputs")
    sub.add_parser("analyse", help="derive → rules → indices → brief → dashboard → export")
    for name in ("derive", "rules", "indices", "backtest", "dashboard", "brief", "weekly", "export", "calendar"):
        sub.add_parser(name)
    lv = sub.add_parser("live", help="refresh intraday quotes + live insights (site/data/live.js)")
    lv.add_argument("--prev", help="previously published live.js (URL or file) to keep intraday history")
    sv = sub.add_parser("serve", help="open the app at http://localhost:8765 (live updates + Update-now button)")
    sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--open", action="store_true", help="open the browser")
    d = sub.add_parser("doctor", help="health check")
    d.add_argument("--fix", action="store_true", help="apply safe automatic fixes")
    ev = sub.add_parser("events", help="list the candidate review queue or set an event's confidence")
    ev.add_argument("action", choices=["queue", "confirm", "reject", "scan"])
    ev.add_argument("event_id", nargs="?")
    a = p.parse_args(argv)

    from .db import connect

    if a.cmd == "serve":
        from .server import serve
        serve(a.port, a.open)
        return 0
    if a.cmd == "run":
        return run_job(a.job, backfill=a.backfill, dry_run=a.dry_run)
    conn = connect()
    try:
        if a.cmd == "init":
            init(conn)
        elif a.cmd == "live":
            from .live import write_live
            print(write_live(conn, a.prev))
        elif a.cmd == "collect":
            from .collectors import Ctx, run_collectors
            init(conn)
            print(run_collectors(conn, a.names, Ctx(run_id=f"manual-{uuid.uuid4().hex[:6]}", backfill=a.backfill)))
        elif a.cmd == "analyse":
            analyse(conn)
        elif a.cmd == "derive":
            from .derive import compute_all
            print(compute_all(conn))
        elif a.cmd == "rules":
            from .rules import evaluate_rules
            evaluate_rules(conn)
        elif a.cmd == "indices":
            from .indices import compute_indices
            print(compute_indices(conn))
        elif a.cmd == "backtest":
            from .indices import run_backtest
            print(run_backtest(conn))
        elif a.cmd == "dashboard":
            from .outputs.site_data import write_site
            print(write_site(conn))
        elif a.cmd == "brief":
            from .outputs.brief import write_brief
            print(write_brief(conn))
        elif a.cmd == "weekly":
            from .outputs.weekly import write_weekly
            print(write_weekly(conn))
        elif a.cmd == "export":
            from .export import export_powerbi
            print(export_powerbi(conn))
        elif a.cmd == "calendar":
            from . import calendar as cal
            cal.refresh(conn)
            print(cal.write_alerts(conn))
        elif a.cmd == "doctor":
            from .doctor import doctor
            res = doctor(conn, fix=a.fix)
            return 1 if res["critical"] else 0
        elif a.cmd == "events":
            from .events import review_queue, scan_candidates, set_confidence
            if a.action == "queue":
                for e in review_queue(conn):
                    print(f"{e['event_id']}  {e['event_date']}  {e['event_type']:<32} outlets={e['n_outlets']}  {e['title_en'][:90]}")
            elif a.action == "scan":
                print(scan_candidates(conn))
            elif a.event_id:
                ok = set_confidence(conn, a.event_id, "confirmed" if a.action == "confirm" else "candidate")
                if a.action == "reject" and ok:
                    conn.execute("DELETE FROM events WHERE event_id=?", (a.event_id,))
                print("ok" if ok else "event not found")
        conn.commit()
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
