"""GDELT DOC 2.0 timelines (no key; >= 6 s between calls; stop for the run after a rate-limit failure)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from urllib.parse import quote

from ..data import catalog
from ..db import add_obs
from ..http import FetchError
from . import collector

API = "https://api.gdeltproject.org/api/v2/doc/doc"
GAP = 10.0


def _calls() -> list[tuple[str, str, str]]:
    out = []
    for sid, m in catalog().items():
        if m.get("source") != "gdelt_doc":
            continue
        mode = "timelinetone" if sid.endswith("_tone") else "timelinevol"
        out.append((sid, m["endpoint"], mode))
    return out


def parse_timeline(j: dict) -> dict[str, float]:
    """Average the points of each calendar day (UTC)."""
    tl = j.get("timeline") or []
    if not tl:
        return {}
    by_day: dict[str, list[float]] = defaultdict(list)
    for p in tl[0].get("data", []):
        d = datetime.strptime(p["date"][:8], "%Y%m%d").date().isoformat()
        by_day[d].append(float(p["value"]))
    return {d: sum(v) / len(v) for d, v in by_day.items()}


ARTLIST_QUERY = "egypt (economy OR pound OR imf OR suez OR rating OR fuel) sourcelang:english"


def collect_articles(conn, ctx) -> int:
    """Recent Egypt headlines from GDELT → news_items (candidates only; not corroborating outlets)."""
    from ..news import store_news

    url = f"{API}?query={quote(ARTLIST_QUERY)}&mode=artlist&format=json&maxrecords=75&timespan=2d&sort=datedesc"
    j = ctx.http.get(url, gap=GAP, backoff=10).json()
    n = 0
    for a in j.get("articles", []):
        seen = a.get("seendate", "")
        pub = datetime.strptime(seen[:15], "%Y%m%dT%H%M%S").isoformat() + "+00:00" if len(seen) >= 15 else None
        n += store_news(conn, f"GDELT: {a.get('domain', '?')}", a.get("url"), a.get("title", ""), None, pub)
    return n


@collector("gdelt")
def collect(conn, ctx) -> int:
    rows = 0
    def last(sid):  # oldest-first, so a rate limit doesn't always starve the same queries
        return conn.execute("SELECT COALESCE(MAX(obs_date),'') FROM observations WHERE series_id=?", (sid,)).fetchone()[0]
    for sid, query, mode in sorted(_calls(), key=lambda c: last(c[0])):
        url = f"{API}?query={quote(query)}&mode={mode}&format=json&timespan=3m"
        try:
            r = ctx.http.get(url, gap=GAP, backoff=10)
            j = r.json()
        except (FetchError, ValueError) as e:
            conn.commit()  # keep what we already got
            raise RuntimeError(f"GDELT stopped after {rows} rows (rate limit or bad reply): {str(e)[:160]}")
        days = parse_timeline(j)
        today = max(days) if days else None
        for d, v in days.items():
            if d == today:
                continue  # skip the still-incomplete current day
            rows += add_obs(conn, sid, d, round(v, 4), unit=catalog()[sid]["unit"],
                            source_name=f"GDELT DOC 2.0 {mode} '{query}'",
                            source_url=url, quality_flag="unofficial",
                            obs_note="daily mean of GDELT timeline points (UTC days)") != "same"
    try:  # headlines for event candidates — nice to have, never fatal
        rows += collect_articles(conn, ctx)
    except (FetchError, ValueError) as e:
        from ..core import get_logger
        get_logger("pulse.gdelt").warning("GDELT article list skipped: %s", str(e)[:160])
    return rows
