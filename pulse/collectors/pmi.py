"""S&P Global PMI press releases (headline only — sub-indices are paid)."""
from __future__ import annotations

import io
import re
from datetime import date, datetime

from bs4 import BeautifulSoup

from ..db import add_obs, save_raw
from . import collector
from .cbe import MONTHS

LIST_URL = "https://www.pmi.spglobal.com/Public/Release/PressReleases"
TARGETS = {"S&P Global Egypt PMI": "pmi", "Riyad Bank Saudi Arabia PMI": "saudi_pmi",
           "S&P Global United Arab Emirates PMI": "uae_pmi"}
PAIR_RE = re.compile(r"(\d{2}\.\d) in (January|February|March|April|May|June|July|August|September|October|"
                     r"November|December)\b")


def parse_pmi_text(text: str, release: date) -> list[tuple[date, float]]:
    """All 'NN.N in <Month>' pairs in the commentary (headline + months it is compared with)."""
    t = re.sub(r"\s+", " ", text)
    out: dict[date, float] = {}
    for v, mon in PAIR_RE.findall(t):
        val = float(v)
        if not 25 <= val <= 75:
            continue
        m = MONTHS[mon.lower()]
        y = release.year if m <= release.month else release.year - 1
        out.setdefault(date(y, m, 1), val)
    return sorted(out.items())


def list_releases(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for item in soup.select("div.listItem"):
        title = item.select_one(".releaseTitle")
        when = item.select_one(".releaseDate")
        a = item.select_one("a[href]")
        if not (title and when and a):
            continue
        name = title.get_text(strip=True)
        if name not in TARGETS:
            continue
        ds = when.get_text(" ", strip=True).replace("\xa0", " ")
        try:
            d = datetime.strptime(" ".join(ds.split()[:3]), "%B %d %Y").date()
        except ValueError:
            continue
        out.append({"series": TARGETS[name], "title": name, "date": d, "url": a["href"]})
    return out


@collector("pmi")
def collect(conn, ctx) -> int:
    import pdfplumber

    r = ctx.http.get(LIST_URL)
    rows = 0
    seen = set()
    for rel in list_releases(r.text):
        if rel["series"] in seen:  # newest first; one release per series is enough
            continue
        seen.add(rel["series"])
        done = conn.execute("SELECT 1 FROM raw_files WHERE url=?", (rel["url"],)).fetchone()
        if done and ctx.has_rows(conn, rel["series"]):
            continue
        pr = ctx.http.get(rel["url"])
        save_raw(conn, f"pmi_{rel['series']}", rel["url"], pr.content, "pdf")
        with pdfplumber.open(io.BytesIO(pr.content)) as doc:
            text = "\n".join((pg.extract_text() or "") for pg in doc.pages[:2])
        for od, v in parse_pmi_text(text, rel["date"]):
            rows += add_obs(conn, rel["series"], od, v, unit="index", source_name=f"S&P Global — {rel['title']}",
                            source_url=rel["url"], quality_flag="official", release_date=rel["date"],
                            obs_note="headline PMI quoted in the press-release commentary") != "same"
    return rows
