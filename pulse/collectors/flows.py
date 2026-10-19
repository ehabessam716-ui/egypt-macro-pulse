"""Foreign investor net flows, read from daily market-wrap articles (free news sites whose robots.txt allow it).

EGX publishes nationality flows on its own site, but that site is behind an anti-bot challenge (MANUAL), so the
same numbers are taken from the press that quotes them. Every value keeps the article URL; quality 'secondary'.
Sign: negative = foreigners were NET SELLERS (money leaving), positive = net buyers. Unit: EGP million.

Series:
  egx_foreign_net   — non-Arab foreign investors, listed stocks, one trading session
  tbill_foreign_net — foreign investors in Egyptian treasury bills (secondary market), when reported
"""
from __future__ import annotations

import html as _html
import re
from datetime import date, datetime, timedelta

from ..core import CAIRO, get_logger
from ..db import add_obs
from . import collector

log = get_logger("pulse.flows")

FEEDS = [  # (outlet, search feed) — WordPress search feeds; both sites allow crawling in robots.txt
    ("Amwal Al Ghad", "https://en.amwalalghad.com/?s=EGX&feed=rss2"),
    ("Amwal Al Ghad", "https://en.amwalalghad.com/?s=foreign+investors&feed=rss2"),
    ("Middle East Observer", "https://meobserver.news/?s=EGX&feed=rss2"),
    ("Amwal Al Ghad", "https://en.amwalalghad.com/?s=Egypt%27s+stocks&feed=rss2"),
]
PAGES = 4  # ~10 articles per feed page
TITLE_HINT = re.compile(r"EGX|stock|bourse|bills?|T-bill|foreign|hot money|equit", re.I)
UNIT = {"bn": 1000.0, "billion": 1000.0, "mn": 1.0, "million": 1.0, "m": 1.0}
NUM = r"(?:EGP|LE|E£)?\s?([\d]{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s?(bn|billion|mn|million|m)\b(?:\s*(?:Egyptian )?pounds?)?"
FOREIGN = r"(?:non-arab\s+)?foreign(?:ers|\s+investors|\s+institutions)?"
PATTERNS = [  # (regex, sign) — first group number, second unit
    (re.compile(FOREIGN + r"[^.;]{0,40}?net\s+(?:sales|selling|sellers)(?:\s+(?:reached|of|totall?ing|amounting\s+to|worth))?\s*" + NUM, re.I), -1),
    (re.compile(r"(?:reported\s+)?foreign\s+net\s+selling\s+(?:reached|of|hit|totall?ed)\s*" + NUM, re.I), -1),
    (re.compile(FOREIGN + r"\s+(?:sold|offloaded)\s+(?:a\s+net\s+)?" + NUM, re.I), -1),
    (re.compile(FOREIGN + r"[^.;]{0,40}?net\s+(?:purchases|buying|buyers)(?:\s+(?:reached|of|totall?ing|amounting\s+to|worth))?\s*" + NUM, re.I), 1),
    (re.compile(r"foreign\s+net\s+buying\s+(?:reached|of|hit|totall?ed)\s*" + NUM, re.I), 1),
    (re.compile(FOREIGN + r"\s+(?:bought|purchased)\s+(?:a\s+net\s+)?" + NUM, re.I), 1),
]
RAW = r"(?:EGP|LE)?\s?(\d{1,3}(?:,\d{3}){2,}(?:\.\d+)?)\s?(?:Egyptian\s+)?(pounds|EGP)"   # 27,012,379,512 pounds
PATTERNS += [
    (re.compile(FOREIGN + r"[^.;]{0,30}?net\s+sellers?\s+(?:with|of|at|worth)\s+" + RAW, re.I), -1),
    (re.compile(FOREIGN + r"[^.;]{0,30}?net\s+buyers?\s+(?:with|of|at|worth)\s+" + RAW, re.I), 1),
]
UNIT.update({"pounds": 1e-6, "egp": 1e-6})
TBILL = re.compile(r"treasury bills?|t-bills?|government debt|debt instruments|local debt|sovereign debt", re.I)
STOCK = re.compile(r"EGX|bourse|stock|shares|equit", re.I)
DAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


def clean(text: str) -> str:
    t = _html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", t)


def session_date(text: str, published: date) -> date:
    """The trading session the article reports: an explicit 'Oct. 1' / '18 October', else the weekday named
    near the top, else the publication day (EGX trades Sun–Thu)."""
    head = text[:1500]
    m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})\b", head)
    if m:
        mon = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(m.group(1)[:3].lower()) + 1
        d = date(published.year, mon, int(m.group(2)))
        if d <= published and (published - d).days < 10:
            return d
    m = re.search(r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b", head)
    if m:
        mon = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"].index(m.group(2).lower()) + 1
        d = date(published.year, mon, int(m.group(1)))
        if d <= published and (published - d).days < 10:
            return d
    m = re.search(r"\b(Sunday|Monday|Tuesday|Wednesday|Thursday)\b", head, re.I)
    if m:
        wd = DAYS[m.group(1).lower()]
        back = (published.weekday() - wd) % 7
        return published - timedelta(days=back)
    return published


ACTOR = re.compile(r"non-Arab foreigners|non-Arab foreign investors|foreigners|foreign investors|Egyptians|Egyptian investors|Arabs|Arab investors", re.I)
AMOUNT = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(billion|million|bn|mn)?\s*(?:Egyptian\s+)?(?:pounds|EGP)?", re.I)


def _respectively(t: str) -> list[tuple[float, str]]:
    """'Arabs and non-Arab foreigners were net buyers with 9,422,965,489 and 307,832,282 pounds, respectively'
    → the foreign figure is matched to its position in the list."""
    out = []
    for m in re.finditer(r"were\s+net\s+(buyers|sellers)", t, re.I):
        end = t.find("respectively", m.end(), m.end() + 300)
        if end < 0:
            continue
        actors = ACTOR.findall(t[max(0, m.start() - 90): m.start()])
        nums = [a for a in AMOUNT.findall(t[m.end(): end]) if any(ch.isdigit() for ch in a[0]) and ("," in a[0] or a[1])]
        if len(actors) < 2 or len(nums) != len(actors):
            continue
        for k, a in enumerate(actors):
            if "foreign" in a.lower():
                num, unit = nums[k]
                v = float(num.replace(",", "")) * (UNIT[unit.lower()] if unit else 1e-6)
                out.append(((1 if m.group(1).lower() == "buyers" else -1) * v, t[max(0, m.start() - 90): end + 12]))
    return out


def parse_flows(text: str, published: date) -> list[dict]:
    """Every foreign net-flow figure in an article → [{series, value (EGP mn, signed), date, quote}]."""
    t = clean(text)
    d = session_date(t, published)
    out, seen = [], set()
    for v, q in _respectively(t):
        out.append({"series": "egx_foreign_net", "value": round(v, 3), "date": d, "quote": q.strip()})
        seen.add(("egx_foreign_net", round(v, 1)))
    for rx, sign in PATTERNS:
        for m in rx.finditer(t):
            num, unit = m.group(1), m.group(2).lower()
            val = sign * float(num.replace(",", "")) * UNIT[unit]
            ctx = t[max(0, m.start() - 250): m.end() + 120]
            series = "tbill_foreign_net" if TBILL.search(ctx) and not STOCK.search(t[max(0, m.start() - 120): m.end() + 60]) else "egx_foreign_net"
            # institutions-only sub-totals are not the headline figure
            if re.search(r"foreign\s+institutions", m.group(0), re.I):
                continue
            if "respectively" in t[m.end(): m.end() + 200] and re.search(r"\band\b", m.group(0)):
                continue
            key = (series, round(val, 1))
            if key in seen:
                continue
            seen.add(key)
            out.append({"series": series, "value": round(val, 3), "date": d, "quote": t[max(0, m.start() - 60): m.end() + 40].strip()})
    # one figure per series per article: the first one reported (the headline total)
    first = {}
    for r in out:
        first.setdefault(r["series"], r)
    return list(first.values())


@collector("flows")
def collect(conn, ctx) -> int:
    import feedparser

    rows, seen = 0, set()
    pages = [(o, f + (f"&paged={n}" if n > 1 else "")) for o, f in FEEDS for n in range(1, PAGES + 1)]
    for outlet, feed in pages:
        try:
            r = ctx.browser.get(feed)
        except Exception as e:  # noqa: BLE001
            log.warning("flows feed %s failed: %s", feed, e)
            continue
        for e in feedparser.parse(r.content).entries[:25]:
            url = e.get("link")
            if not url or url in seen or not TITLE_HINT.search(e.get("title", "")):
                continue
            seen.add(url)
            try:
                pub = datetime(*e.published_parsed[:6]).date() if e.get("published_parsed") else date.today()
            except Exception:  # noqa: BLE001
                pub = date.today()
            if (date.today() - pub).days > 45:
                continue
            body = " ".join(c.get("value", "") for c in e.get("content", [])) or ""
            if not re.search(r"net\s+(?:sell|buy|sales|purchas)|foreign\w*\s+(?:sold|bought)", clean(body), re.I):
                try:
                    body = ctx.browser.get(url).text
                except Exception as ex:  # noqa: BLE001
                    log.warning("flows article %s failed: %s", url, ex)
                    continue
            for f in parse_flows(e.get("title", "") + ". " + body, pub):
                res = add_obs(conn, f["series"], f["date"], f["value"], unit="EGP mn", source_name=f"{outlet} (market report, secondary)",
                              source_url=url, quality_flag="secondary", release_date=pub,
                              obs_note=("negative = foreign net selling; quote: " + f["quote"])[:480])
                rows += res != "same"
    return rows
