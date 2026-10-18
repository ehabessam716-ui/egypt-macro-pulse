"""Paths, time helpers and config loading shared by every module."""
from __future__ import annotations

import logging
import sys
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
RAW = DATA / "raw"
MANUAL_DIR = DATA / "manual"
MANUAL_XLSX = MANUAL_DIR / "manual_inputs.xlsx"
DB_PATH = DATA / "pulse.db"
SITE = ROOT / "site"
BRIEFS = ROOT / "briefs"
EXPORTS = ROOT / "exports"
REPORTS = ROOT / "reports"
LOGS = ROOT / "logs"

CAIRO = ZoneInfo("Africa/Cairo")
UTC = timezone.utc

# CBE / EGX week: Sunday–Thursday. Python weekday(): Mon=0 … Sun=6.
EGYPT_BUSINESS_DAYS = {6, 0, 1, 2, 3}
GLOBAL_BUSINESS_DAYS = {0, 1, 2, 3, 4}

DERIVED_SOURCE = "Egypt Macro Pulse (derived)"


def now_cairo() -> datetime:
    return datetime.now(CAIRO)


def today_cairo() -> date:
    return now_cairo().date()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def is_business_day(d: date, calendar: str = "egypt") -> bool:
    if calendar == "egypt":
        return d.weekday() in EGYPT_BUSINESS_DAYS
    if calendar == "global":
        return d.weekday() in GLOBAL_BUSINESS_DAYS
    return True


def business_days_between(start: date, end: date, calendar: str = "egypt") -> int:
    """Business days strictly after `start` up to and including `end`."""
    if end <= start:
        return 0
    n, d = 0, start
    while d < end:
        d += timedelta(days=1)
        if is_business_day(d, calendar):
            n += 1
    return n


def period_end(obs: date, frequency: str) -> date:
    """Last calendar day of the period an observation describes."""
    import calendar as _cal

    f = (frequency or "daily").lower()
    if f in ("monthly",):
        return date(obs.year, obs.month, _cal.monthrange(obs.year, obs.month)[1])
    if f == "quarterly":
        q_end_month = ((obs.month - 1) // 3 + 1) * 3
        return date(obs.year, q_end_month, _cal.monthrange(obs.year, q_end_month)[1])
    if f == "fiscal_year":  # Egypt FY: 1 Jul – 30 Jun; obs_date is 1 Jul of the start year
        return date(obs.year + 1, 6, 30)
    if f == "annual":
        return date(obs.year, 12, 31)
    return obs


def fy_label(start_year: int) -> str:
    return f"FY{start_year}/{str(start_year + 1)[-2:]}"


@lru_cache(maxsize=None)
def load_yaml(name: str) -> dict:
    path = CONFIG / name
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def reload_configs() -> None:
    load_yaml.cache_clear()


def get_logger(name: str = "pulse") -> logging.Logger:
    base = logging.getLogger("pulse")
    if not base.handlers:
        _configure(base)
    return logging.getLogger(name)


def _configure(log: logging.Logger) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOGS / "pulse.log", encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if sys.stdout is not None:  # pythonw (scheduled tasks) has no console
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(sh)
    log.setLevel(logging.INFO)
    log.propagate = False
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
