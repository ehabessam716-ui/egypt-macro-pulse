"""News RSS feeds → news_items (used for event candidates; never for values)."""
from __future__ import annotations

from datetime import datetime, timezone

import feedparser

from ..core import load_yaml
from ..news import store_news
from . import collector


def feeds() -> list[dict]:
    return [s for s in load_yaml("sources.yaml")["sources"] if s["kind"] == "rss" and s["access"] != "MANUAL"]


@collector("rss")
def collect(conn, ctx) -> int:
    rows, errors = 0, []
    for f in feeds():
        try:
            r = ctx.http.get(f["url"])
        except Exception as e:  # noqa: BLE001
            errors.append(f"{f['id']}: {e}")
            continue
        parsed = feedparser.parse(r.content)
        for e in parsed.entries:
            t = e.get("published_parsed") or e.get("updated_parsed")
            pub = datetime(*t[:6], tzinfo=timezone.utc).isoformat() if t else None
            summary = e.get("summary", "")
            rows += store_news(conn, f.get("outlet", f["name"]), e.get("link"), e.get("title", ""), summary, pub)
    if errors and rows == 0 and len(errors) == len(feeds()):
        raise RuntimeError("; ".join(errors))
    return rows
