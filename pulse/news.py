"""News item storage shared by the RSS and CBE collectors."""
from __future__ import annotations

import sqlite3

from .core import utc_now_iso


def store_news(conn: sqlite3.Connection, outlet: str, url: str, title: str, summary: str | None,
               published_at: str | None) -> bool:
    if not url or not title:
        return False
    cur = conn.execute(
        "INSERT OR IGNORE INTO news_items(url,outlet,title,summary,published_at,fetched_at) VALUES (?,?,?,?,?,?)",
        (url, outlet, title.strip(), (summary or "")[:2000], published_at, utc_now_iso()))
    return cur.rowcount > 0
