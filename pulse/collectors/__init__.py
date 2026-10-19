"""Collector registry. Each collector: fn(conn, ctx) -> rows added. Failures are logged, never fatal."""
from __future__ import annotations

import sqlite3
import traceback
from dataclasses import dataclass, field
from typing import Callable

from ..core import get_logger, utc_now_iso
from ..db import log_fetch
from ..http import Http

log = get_logger("pulse.collect")


@dataclass
class Ctx:
    run_id: str
    http: Http = field(default_factory=lambda: Http(browser_ua=False))
    browser: Http = field(default_factory=lambda: Http(browser_ua=True, min_gap=2.5))
    backfill: bool = False

    def has_rows(self, conn: sqlite3.Connection, series_id: str) -> bool:
        return conn.execute("SELECT 1 FROM observations WHERE series_id=? LIMIT 1", (series_id,)).fetchone() is not None


Collector = Callable[[sqlite3.Connection, Ctx], int]
REGISTRY: dict[str, Collector] = {}


def collector(name: str):
    def wrap(fn: Collector) -> Collector:
        REGISTRY[name] = fn
        return fn
    return wrap


# Which collectors each scheduled job runs (SPEC §10).
JOBS = {
    "daily": ["cbe_fx", "cbe_rates", "cbe_cpi", "cbe_auctions", "cbe_news", "yahoo", "gold_eg", "pmi",
              "portwatch", "rss", "gdelt", "flows"],
    "global": ["fred", "yahoo", "intl", "portwatch"],
    "gpr": ["gpr"],
    "weekly": ["cbe_news", "portwatch", "intl", "fomc", "imf_sdmx", "cbe_mpc_hist"],
    "calendar": ["fomc"],
}
JOBS["all"] = sorted({c for v in JOBS.values() for c in v} | {"fred", "gpr", "intl", "fomc", "imf_sdmx", "cbe_mpc_hist"})


def _load_all() -> None:
    # import modules for their @collector side effects
    from . import cbe, flows, fred, imf_sdmx, gdelt, gold_eg, gpr, intl, pmi, portwatch, rss, yahoo  # noqa: F401
    from .. import calendar  # noqa: F401  (registers the 'fomc' collector)


def run_collectors(conn: sqlite3.Connection, names: list[str], ctx: Ctx) -> dict[str, dict]:
    _load_all()
    results: dict[str, dict] = {}
    for name in names:
        fn = REGISTRY.get(name)
        if fn is None:
            log.warning("unknown collector %s", name)
            continue
        started = utc_now_iso()
        try:
            rows = fn(conn, ctx)
            conn.commit()
            log_fetch(conn, ctx.run_id, name, started, "ok", rows)
            results[name] = {"status": "ok", "rows": rows}
            log.info("collector %-13s ok   rows=%s", name, rows)
        except Exception as e:  # noqa: BLE001 — a failing source never stops a run
            conn.rollback()
            err = f"{type(e).__name__}: {e}"
            log_fetch(conn, ctx.run_id, name, started, "error", 0, err + "\n" + traceback.format_exc()[-1500:])
            results[name] = {"status": "error", "rows": 0, "error": err[:300]}
            log.warning("collector %-13s FAIL %s", name, err[:300])
        conn.commit()
    return results
