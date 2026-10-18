"""Series catalog + a read-only, point-in-time view of the observations table.

`DataView(conn, as_of)` only sees data that was available on `as_of`
(release_date, or period end + release lag when the release date is unknown),
so the backtest never uses information from the future.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache

import pandas as pd

from .core import business_days_between, load_yaml, period_end, today_cairo
from .db import QUALITY_RANK

DEFAULT_LAG = {"daily": 0, "weekly": 3, "monthly": 15, "quarterly": 75, "fiscal_year": 120,
               "annual": 120, "per_auction": 0, "event": 0}


@lru_cache(maxsize=1)
def catalog() -> dict[str, dict]:
    cfg = load_yaml("series.yaml")
    defaults = cfg.get("defaults", {}).get("stale_after_days", {})
    out = {}
    for s in cfg["series"]:
        s = dict(s)
        s.setdefault("calendar", "all")
        s.setdefault("step", False)
        s.setdefault("release_lag_days", DEFAULT_LAG.get(s["frequency"], 0))
        s.setdefault("stale_after_days", defaults.get(s["frequency"], 45))
        out[s["id"]] = s
    return out


def sync_catalog(conn: sqlite3.Connection) -> int:
    rows = 0
    for s in catalog().values():
        conn.execute(
            """INSERT INTO series_catalog(series_id,name_en,name_ar,domain,frequency,unit,source,endpoint,fallback,
               access,definition_note,release_lag_days,stale_after_days,calendar,step)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(series_id) DO UPDATE SET name_en=excluded.name_en, name_ar=excluded.name_ar,
               domain=excluded.domain, frequency=excluded.frequency, unit=excluded.unit, source=excluded.source,
               endpoint=excluded.endpoint, fallback=excluded.fallback, access=excluded.access,
               definition_note=excluded.definition_note, release_lag_days=excluded.release_lag_days,
               stale_after_days=excluded.stale_after_days, calendar=excluded.calendar, step=excluded.step""",
            (s["id"], s["name_en"], s["name_ar"], s["domain"], s["frequency"], s.get("unit"), s.get("source"),
             s.get("endpoint"), s.get("fallback"), s["access"], s.get("definition_note"), s["release_lag_days"],
             s["stale_after_days"], s["calendar"], int(bool(s["step"]))))
        rows += 1
    return rows


def staleness(sid: str, obs_date: date, as_of: date) -> tuple[int, int]:
    """Return (level, age). level 0 fresh, 1 stale (orange), 2 very stale (red, excluded from indices)."""
    meta = catalog().get(sid, {"frequency": "daily", "stale_after_days": 3, "calendar": "all"})
    limit = meta["stale_after_days"]
    if meta["frequency"] == "daily":
        age = business_days_between(obs_date, as_of, meta.get("calendar", "all"))
    elif meta["frequency"] in ("event",) or meta.get("step"):
        return 0, (as_of - obs_date).days
    else:
        age = (as_of - period_end(obs_date, meta["frequency"])).days
    if age > 2 * limit:
        return 2, age
    if age > limit:
        return 1, age
    return 0, age


@dataclass
class Obs:
    series_id: str
    date: date
    value: float
    source_name: str
    source_url: str
    quality: str
    release_date: str | None = None
    retrieved_at: str | None = None
    obs_time: str | None = None
    note: str | None = None
    stale: int = 0
    age: int = 0
    conflict: bool = False
    via_fallback: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def meta(self) -> dict:
        return catalog().get(self.series_id, {})

    def cite(self) -> dict:
        return {"series": self.series_id, "value": self.value, "obs_date": self.date.isoformat(),
                "source": self.source_name, "url": self.source_url, "release_date": self.release_date,
                "retrieved_at": self.retrieved_at, "quality": self.quality, "stale": self.stale}


_BASE_CACHE: dict = {}


def load_base(conn: sqlite3.Connection) -> pd.DataFrame:
    """All non-null observations with an 'avail' date, cached until the table changes (saves memory)."""
    sig = (conn.execute("PRAGMA database_list").fetchone()[2],) + tuple(
        conn.execute("SELECT COUNT(*), MAX(rowid), COALESCE(MAX(retrieved_at),'') FROM observations").fetchone())
    if _BASE_CACHE.get("sig") == sig:
        return _BASE_CACHE["df"]
    _BASE_CACHE.clear()
    df = _load_base(conn)
    _BASE_CACHE.update(sig=sig, df=df)
    return df


def _load_base(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT series_id, obs_date, value, release_date, retrieved_at, source_name, source_url, vintage, "
        "quality_flag, obs_time, obs_note, conflict FROM observations WHERE value IS NOT NULL", conn)
    if df.empty:
        df["avail"] = []
        return df
    df["obs_date"] = pd.to_datetime(df["obs_date"]).dt.date
    df["rank"] = df["quality_flag"].map(QUALITY_RANK).fillna(9).astype("int8")
    for col in ("series_id", "source_name", "source_url", "quality_flag"):
        df[col] = df[col].astype("category")  # few distinct values → far less memory
    cat = catalog()
    keys = df[["series_id", "obs_date"]].drop_duplicates()
    avail = {}
    for sid, od in keys.itertuples(index=False):
        m = cat.get(sid, {"frequency": "daily", "release_lag_days": 0})
        avail[(sid, od)] = period_end(od, m["frequency"]) + timedelta(days=int(m["release_lag_days"]))
    est = [avail[(a, b)] for a, b in zip(df["series_id"], df["obs_date"])]
    rel = pd.to_datetime(df["release_date"], errors="coerce").dt.date
    df["avail"] = [r if isinstance(r, date) and not pd.isna(r) else e for r, e in zip(rel, est)]
    return df.sort_values(["series_id", "obs_date", "rank", "vintage"], ascending=[True, True, True, False])


class DataView:
    def __init__(self, conn: sqlite3.Connection, as_of: date | None = None, point_in_time: bool = False,
                 base: pd.DataFrame | None = None):
        self.conn = conn
        self.as_of = as_of or today_cairo()
        self.point_in_time = point_in_time
        df = load_base(conn) if base is None else base
        if point_in_time and not df.empty:
            df = df[df["avail"] <= self.as_of]
        # best row per (series, date): best quality, then latest vintage (base is pre-sorted)
        self._df = df.drop_duplicates(["series_id", "obs_date"], keep="first").reset_index(drop=True) if not df.empty else df
        self._cache: dict[str, pd.DataFrame] = {}

    def frame(self, sid: str, include_future: bool = False) -> pd.DataFrame:
        key = f"{sid}|{include_future}"
        if key not in self._cache:
            if self._df.empty:
                self._cache[key] = self._df
            else:
                d = self._df[self._df["series_id"] == sid]
                if not include_future:
                    d = d[d["obs_date"] <= self.as_of]
                self._cache[key] = d
        return self._cache[key]

    def series(self, sid: str, include_future: bool = False) -> pd.Series:
        d = self.frame(sid, include_future)
        if d.empty:
            return pd.Series(dtype=float, index=pd.DatetimeIndex([]), name=sid)
        s = pd.Series(d["value"].astype(float).values, index=pd.to_datetime(d["obs_date"]), name=sid)
        return s.sort_index()

    def has(self, sid: str) -> bool:
        return not self.frame(sid).empty

    def _obs_from_row(self, sid: str, r) -> Obs:
        level, age = staleness(sid, r["obs_date"], self.as_of)
        return Obs(series_id=sid, date=r["obs_date"], value=float(r["value"]), source_name=r["source_name"],
                   source_url=r["source_url"], quality=r["quality_flag"], release_date=r["release_date"],
                   retrieved_at=r["retrieved_at"], obs_time=r["obs_time"], note=r["obs_note"],
                   stale=level, age=age, conflict=bool(r["conflict"]))

    def latest(self, sid: str) -> Obs | None:
        d = self.frame(sid)
        if d.empty:
            return None
        return self._obs_from_row(sid, d.iloc[-1])

    def nth_latest(self, sid: str, n: int) -> Obs | None:
        d = self.frame(sid)
        if len(d) <= n:
            return None
        return self._obs_from_row(sid, d.iloc[-1 - n])

    def fresh(self, sid: str, max_level: int = 1) -> Obs | None:
        """Latest observation if not too stale (default: excludes red/level-2)."""
        o = self.latest(sid)
        return o if o is not None and o.stale <= max_level else None

    def resolved(self, sid: str, max_level: int = 1) -> Obs | None:
        """Primary series if fresh enough, else its configured fallback (SPEC §3 'fallback')."""
        o = self.latest(sid)
        if o is not None and o.stale <= max_level:
            return o
        fb = catalog().get(sid, {}).get("fallback")
        if fb and fb in catalog():
            f = self.latest(fb)
            if f is not None and f.stale <= max_level:
                f.via_fallback = sid
                return f
        return o if (o is not None and o.stale <= max_level) else None

    def value_at(self, sid: str, when: date) -> Obs | None:
        """Last observation on or before `when` (for step series like policy rates)."""
        d = self.frame(sid)
        if d.empty:
            return None
        d = d[d["obs_date"] <= when]
        if d.empty:
            return None
        return self._obs_from_row(sid, d.iloc[-1])

    def all_ids(self) -> list[str]:
        return sorted(self._df["series_id"].unique()) if not self._df.empty else []
