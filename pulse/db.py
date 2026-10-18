"""SQLite storage (data/pulse.db). Schema follows SPEC §4, plus a few audit columns.

Values are never invented: a missing value is stored as NULL with a `null_reason`.
Revisions become new vintages; disagreeing sources are both kept and flagged `conflict`.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from .core import DB_PATH, RAW, utc_now_iso

QUALITY_FLAGS = ("official", "secondary", "unofficial", "manual", "derived")
# Lower = preferred when two rows describe the same series/date.
QUALITY_RANK = {"official": 0, "derived": 1, "manual": 2, "secondary": 3, "unofficial": 4}
CONFLICT_TOLERANCE = 0.005  # 0.5% (SPEC §11)

SCHEMA = """
CREATE TABLE IF NOT EXISTS series_catalog(
  series_id TEXT PRIMARY KEY, name_en TEXT, name_ar TEXT, domain TEXT, frequency TEXT, unit TEXT,
  source TEXT, endpoint TEXT, fallback TEXT, access TEXT, definition_note TEXT,
  release_lag_days INTEGER, stale_after_days INTEGER, calendar TEXT, step INTEGER DEFAULT 0);

CREATE TABLE IF NOT EXISTS observations(
  series_id TEXT NOT NULL, obs_date TEXT NOT NULL, value REAL NULL, unit TEXT,
  release_date TEXT, retrieved_at TEXT NOT NULL, source_name TEXT NOT NULL, source_url TEXT NOT NULL,
  vintage TEXT NOT NULL,
  quality_flag TEXT NOT NULL CHECK (quality_flag IN ('official','secondary','unofficial','manual','derived')),
  null_reason TEXT, obs_time TEXT, obs_note TEXT, conflict INTEGER DEFAULT 0,
  PRIMARY KEY(series_id, obs_date, vintage),
  CHECK (value IS NOT NULL OR null_reason IS NOT NULL));
CREATE INDEX IF NOT EXISTS ix_obs_series ON observations(series_id, obs_date);

CREATE TABLE IF NOT EXISTS raw_files(
  file_id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, url TEXT, sha256 TEXT, retrieved_at TEXT, path TEXT);

CREATE TABLE IF NOT EXISTS fetch_log(
  run_id TEXT, source TEXT, started_at TEXT, finished_at TEXT, status TEXT, rows_added INTEGER, error TEXT);

CREATE TABLE IF NOT EXISTS calendar(
  event_date TEXT NOT NULL, event_time_cairo TEXT, kind TEXT NOT NULL, series_id TEXT, description TEXT,
  status TEXT CHECK (status IN ('scheduled','confirmed','done','moved')), source_url TEXT,
  PRIMARY KEY(event_date, kind, description));

CREATE TABLE IF NOT EXISTS event_types(
  event_type TEXT PRIMARY KEY, default_severity INTEGER, default_direction INTEGER,
  default_half_life_days REAL, affects_subindex TEXT, description TEXT);

CREATE TABLE IF NOT EXISTS events(
  event_id TEXT PRIMARY KEY, event_date TEXT NOT NULL, event_type TEXT NOT NULL, domain TEXT,
  title_en TEXT, title_ar TEXT,
  severity INTEGER CHECK (severity BETWEEN 1 AND 5),
  direction INTEGER CHECK (direction IN (-1,0,1)),
  half_life_days REAL, expires_at TEXT,
  confidence TEXT CHECK (confidence IN ('confirmed','reported','candidate')),
  source_name TEXT, source_url TEXT NOT NULL,
  entered_by TEXT CHECK (entered_by IN ('manual','auto_candidate')), notes TEXT,
  created_at TEXT, updated_at TEXT);

CREATE TABLE IF NOT EXISTS event_sources(
  event_id TEXT, outlet TEXT, url TEXT, title TEXT, published_at TEXT,
  PRIMARY KEY(event_id, url));

CREATE TABLE IF NOT EXISTS news_items(
  url TEXT PRIMARY KEY, outlet TEXT, title TEXT, summary TEXT, published_at TEXT, fetched_at TEXT,
  matched_types TEXT);

CREATE TABLE IF NOT EXISTS rule_hits(
  run_date TEXT, rule_id TEXT, fired INTEGER, strength REAL, direction REAL, inputs_json TEXT,
  explanation_en TEXT, explanation_ar TEXT, concept_tag TEXT, evaluable INTEGER DEFAULT 1,
  PRIMARY KEY(run_date, rule_id));

CREATE TABLE IF NOT EXISTS index_values(
  run_date TEXT, index_id TEXT, value REAL, components_json TEXT, coverage_pct REAL, kind TEXT DEFAULT 'live',
  PRIMARY KEY(run_date, index_id, kind));
"""


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session(path: Path | str | None = None):
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _iso(d: Any) -> str | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    s = str(d)
    return s[:10]


def _same(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def add_obs(conn: sqlite3.Connection, series_id: str, obs_date: Any, value: float | None, *,
            unit: str | None, source_name: str, source_url: str, quality_flag: str,
            release_date: Any = None, obs_time: str | None = None, null_reason: str | None = None,
            obs_note: str | None = None, retrieved_at: str | None = None) -> str:
    """Insert one observation. Returns 'new', 'same', 'revised' or 'conflict'."""
    if quality_flag not in QUALITY_FLAGS:
        raise ValueError(f"bad quality_flag {quality_flag!r}")
    if not source_url:
        raise ValueError(f"{series_id}: every observation needs a source_url")
    if value is not None:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            value, null_reason = None, null_reason or "non-finite value from source"
    if value is None and not null_reason:
        raise ValueError(f"{series_id} {obs_date}: NULL value needs a null_reason")
    od = _iso(obs_date)
    retrieved_at = retrieved_at or utc_now_iso()
    rows = conn.execute(
        "SELECT * FROM observations WHERE series_id=? AND obs_date=? ORDER BY vintage DESC",
        (series_id, od)).fetchall()
    same_src = [r for r in rows if r["source_name"] == source_name]
    if same_src:
        last = same_src[0]
        if _same(last["value"], value):
            if obs_time and not last["obs_time"]:
                conn.execute("UPDATE observations SET obs_time=? WHERE series_id=? AND obs_date=? AND vintage=?",
                             (obs_time, series_id, od, last["vintage"]))
            return "same"
        if value is None:  # never overwrite a real value with a NULL
            return "same"
    vintage = retrieved_at
    n = 1
    while any(r["vintage"] == vintage for r in rows):
        n += 1
        vintage = f"{retrieved_at}#{n}"
    conflict = 0
    others = [r for r in rows if r["source_name"] != source_name and r["value"] is not None]
    if value is not None:
        for r in others:
            base = abs(r["value"]) or 1.0
            if abs(r["value"] - value) / base > CONFLICT_TOLERANCE:
                conflict = 1
                conn.execute("UPDATE observations SET conflict=1 WHERE series_id=? AND obs_date=? AND vintage=?",
                             (series_id, od, r["vintage"]))
    conn.execute(
        """INSERT INTO observations(series_id, obs_date, value, unit, release_date, retrieved_at, source_name,
           source_url, vintage, quality_flag, null_reason, obs_time, obs_note, conflict)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (series_id, od, value, unit, _iso(release_date), retrieved_at, source_name, source_url, vintage,
         quality_flag, null_reason if value is None else None, obs_time, obs_note, conflict))
    if conflict:
        return "conflict"
    return "revised" if same_src else "new"


def add_many(conn: sqlite3.Connection, rows: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        r = dict(r)
        res = add_obs(conn, r.pop("series_id"), r.pop("obs_date"), r.pop("value"), **r)
        counts[res] = counts.get(res, 0) + 1
    return counts


def save_raw(conn: sqlite3.Connection | None, source: str, url: str, content: bytes, ext: str) -> Path:
    """Cache a raw response under data/raw/<YYYY-MM-DD>/ and register it in raw_files."""
    sha = hashlib.sha256(content).hexdigest()
    day = utc_now_iso()[:10]
    folder = RAW / day
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{source}_{sha[:12]}.{ext.lstrip('.')}"
    if not path.exists():
        path.write_bytes(content)
    if conn is not None:
        exists = conn.execute("SELECT 1 FROM raw_files WHERE sha256=? AND source=?", (sha, source)).fetchone()
        if not exists:
            conn.execute("INSERT INTO raw_files(source,url,sha256,retrieved_at,path) VALUES (?,?,?,?,?)",
                         (source, url, sha, utc_now_iso(), str(path)))
    return path


def log_fetch(conn: sqlite3.Connection, run_id: str, source: str, started_at: str, status: str,
              rows_added: int = 0, error: str | None = None) -> None:
    conn.execute("INSERT INTO fetch_log VALUES (?,?,?,?,?,?,?)",
                 (run_id, source, started_at, utc_now_iso(), status, rows_added, (error or "")[:2000] or None))


def to_json(obj: Any) -> str:
    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if hasattr(o, "item"):
            return o.item()
        return str(o)
    return json.dumps(obj, ensure_ascii=False, default=default)
