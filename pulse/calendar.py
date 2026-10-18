"""Release calendar: seeded dates, generated recurring estimates, FOMC page check, 48-hour alerts."""
from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .collectors import collector
from .core import CAIRO, REPORTS, business_days_between, is_business_day, load_yaml, now_cairo, today_cairo

FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
ET = ZoneInfo("America/New_York")


def _to_cairo(d: date, hhmm: str, tz: ZoneInfo) -> str:
    h, m = map(int, hhmm.split(":"))
    return datetime.combine(d, time(h, m), tzinfo=tz).astimezone(CAIRO).strftime("%H:%M")


def _upsert(conn, d: date, t: str | None, kind: str, sid: str | None, desc: str, status: str, url: str,
            keep_status: bool = True) -> None:
    if kind in ("fomc", "mpc"):  # one row per meeting: merge rows that differ only by description
        for old in conn.execute("SELECT description, status FROM calendar WHERE event_date=? AND kind=? AND description<>?",
                                (d.isoformat(), kind, desc)).fetchall():
            if old["status"] in ("confirmed", "done") and status == "scheduled":
                status = old["status"]
            conn.execute("DELETE FROM calendar WHERE event_date=? AND kind=? AND description=?", (d.isoformat(), kind, old["description"]))
    row = conn.execute("SELECT status FROM calendar WHERE event_date=? AND kind=? AND description=?",
                       (d.isoformat(), kind, desc)).fetchone()
    if row and keep_status and row["status"] in ("confirmed", "done") and status == "scheduled":
        status = row["status"]
    conn.execute("""INSERT INTO calendar(event_date,event_time_cairo,kind,series_id,description,status,source_url)
                    VALUES (?,?,?,?,?,?,?) ON CONFLICT(event_date,kind,description) DO UPDATE SET
                    event_time_cairo=excluded.event_time_cairo, status=excluded.status, source_url=excluded.source_url""",
                 (d.isoformat(), t, kind, sid, desc, status, url))


def nth_business_day(year: int, month: int, n: int, cal: str) -> date:
    d = date(year, month, 1)
    count = 0
    while True:
        if is_business_day(d, cal):
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)


def generate_recurring(start: date, days: int = 100) -> list[dict]:
    out = []
    end = start + timedelta(days=days)
    for item in load_yaml("calendar_2026.yaml").get("recurring", []):
        rule = item["rule"]
        if "weekday" in rule:
            d = start
            while d <= end:
                if d.weekday() == rule["weekday"]:
                    t = _to_cairo(d, rule["time_et"], ET) if rule.get("time_et") else item.get("time")
                    out.append({**item, "date": d, "time": t})
                d += timedelta(days=1)
            continue
        y, m = start.year, start.month
        while date(y, m, 1) <= end:
            if "monthday" in rule:
                d = date(y, m, rule["monthday"])
            else:
                d = nth_business_day(y, m, rule["business_day"], rule.get("calendar", "global"))
            if start <= d <= end:
                out.append({**item, "date": d})
            m += 1
            if m > 12:
                y, m = y + 1, 1
    return out


def refresh(conn) -> int:
    n = 0
    today = today_cairo()
    for it in load_yaml("calendar_2026.yaml").get("fixed", []):
        d = it["date"] if isinstance(it["date"], date) else date.fromisoformat(str(it["date"]))
        t = it.get("time")
        if it["kind"] == "fomc" and not t:
            t = _to_cairo(d, "14:00", ET)
        status = it.get("status", "scheduled")
        if status == "scheduled" and d < today and it["kind"] in ("mpc", "fomc"):
            status = "done"
        _upsert(conn, d, t, it["kind"], it.get("series_id"), it["description"], status, it["source_url"])
        n += 1
    for it in generate_recurring(today - timedelta(days=7)):
        status = "done" if it["date"] < today else "scheduled"
        _upsert(conn, it["date"], it.get("time"), it["kind"], it.get("series_id"), it["description"], status,
                it["source_url"], keep_status=False)
        n += 1
    return n


def upcoming(conn, days: int = 14, start: date | None = None) -> list[dict]:
    start = start or today_cairo()
    rows = conn.execute("SELECT * FROM calendar WHERE event_date>=? AND event_date<=? ORDER BY event_date, event_time_cairo",
                        (start.isoformat(), (start + timedelta(days=days)).isoformat())).fetchall()
    return [dict(r) for r in rows]


def alerts_48h(conn) -> list[dict]:
    now = now_cairo()
    out = []
    for r in upcoming(conn, days=3):
        t = r["event_time_cairo"] or "09:00"
        when = datetime.combine(date.fromisoformat(r["event_date"]), time(*map(int, t.split(":"))), tzinfo=CAIRO)
        if now <= when <= now + timedelta(hours=48):
            out.append(r)
    return out


def write_alerts(conn) -> str:
    al = alerts_48h(conn)
    REPORTS.mkdir(exist_ok=True)
    lines = [f"# Release alerts — next 48 hours (generated {now_cairo():%Y-%m-%d %H:%M} Cairo)", ""]
    if not al:
        lines.append("No scheduled releases in the next 48 hours.")
    for r in al:
        lines.append(f"- **{r['event_date']} {r['event_time_cairo'] or ''}** — {r['description']} "
                     f"[{r['status']}] ({r['source_url']})")
    path = REPORTS / "alerts_next48h.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


MONTH_NUM = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"], 1)}


def parse_fomc(html: str) -> list[date]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for panel in soup.select("div.panel"):
        hd = panel.find(["h4", "h5"])
        m = re.match(r"(\d{4}) FOMC Meetings", hd.get_text(strip=True) if hd else "")
        if not m:
            continue
        year = int(m.group(1))
        for row in panel.select("div.fomc-meeting"):
            mon = row.select_one(".fomc-meeting__month")
            day = row.select_one(".fomc-meeting__date")
            if not (mon and day):
                continue
            mtxt = mon.get_text(strip=True).split("/")[-1]
            dm = re.match(r"(\d{1,2})(?:-(\d{1,2}))?", day.get_text(strip=True))
            if mtxt not in MONTH_NUM or not dm or "notation" in day.get_text():
                continue
            last = int(dm.group(2) or dm.group(1))
            month = MONTH_NUM[mtxt]
            if dm.group(2) and int(dm.group(2)) < int(dm.group(1)):  # spans month end, e.g. Apr/May 30-1
                month = MONTH_NUM.get(mon.get_text(strip=True).split("/")[-1], month)
            out.append(date(year, month, last))
    return out


@collector("fomc")
def collect_fomc(conn, ctx) -> int:
    r = ctx.http.get(FOMC_URL)
    meetings = parse_fomc(r.text)
    if not meetings:
        raise RuntimeError("no FOMC meetings parsed from the Fed calendar page")
    n = 0
    for d in meetings:
        if d < today_cairo() - timedelta(days=400):
            continue
        row = conn.execute("SELECT description FROM calendar WHERE kind='fomc' AND event_date=?", (d.isoformat(),)).fetchone()
        desc = row["description"] if row else "FOMC decision"
        status = "done" if d < today_cairo() else "confirmed"
        _upsert(conn, d, _to_cairo(d, "14:00", ET), "fomc", "fed_funds", desc, status, FOMC_URL, keep_status=False)
        n += 1
    return n


def next_business_day(d: date, cal: str = "egypt") -> date:
    d += timedelta(days=1)
    while not is_business_day(d, cal):
        d += timedelta(days=1)
    return d


__all__ = ["refresh", "upcoming", "alerts_48h", "write_alerts", "generate_recurring", "parse_fomc",
           "business_days_between", "next_business_day"]
