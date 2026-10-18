"""Phase 0 — verify every source in config/sources.yaml before any collector is written.

Writes:
  reports/phase0_source_audit.md    human-readable audit table
  reports/phase0_source_audit.json  full machine-readable results
  data/raw/phase0/<id>.*            raw samples kept for audit

Usage:
  python scripts/verify_sources.py              # all sources
  python scripts/verify_sources.py gpr_monthly  # only the given ids
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # optional
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
CAIRO = ZoneInfo("Africa/Cairo")
RAW_DIR = ROOT / "data" / "raw" / "phase0"
REPORT_DIR = ROOT / "reports"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EgyptMacroPulse/0.1 (personal learning tool; source audit)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")
TIMEOUT = 30
MIN_GAP_PER_HOST = 2.0   # seconds between requests to the same host
GDELT_GAP = 6.0

sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class Result:
    id: str
    name: str
    access: str
    status: str = "PENDING"           # OK / BLOCKED / PAID / LOGIN / MOVED / MANUAL
    http_status: int | None = None
    content_type: str | None = None
    last_modified: str | None = None
    final_url: str | None = None
    needs_key: bool = False
    frequency_observed: str | None = None
    latest_obs: str | None = None
    sample: str | None = None
    robots_allowed: bool | None = None
    notes: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


class Http:
    """Polite session: per-host spacing, one retry with backoff."""

    def __init__(self) -> None:
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "en,ar;q=0.8"})
        self.last: dict[str, float] = {}

    def get(self, url: str, gap: float = MIN_GAP_PER_HOST, **kw) -> requests.Response:
        host = urlparse(url).netloc
        wait = self.last.get(host, 0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        tries = 3
        for attempt in range(tries):
            try:
                r = self.s.get(url, timeout=TIMEOUT, allow_redirects=True, **kw)
                self.last[host] = time.monotonic()
                if r.status_code in (429, 502, 503, 504) and attempt < tries - 1:
                    time.sleep(max(gap, 5) * 2 * (attempt + 1))  # exponential-ish backoff
                    continue
                if "charset" not in r.headers.get("Content-Type", "").lower():
                    r.encoding = r.apparent_encoding
                return r
            except requests.RequestException:
                self.last[host] = time.monotonic()
                if attempt == tries - 1:
                    raise
                time.sleep(gap * 2 * (attempt + 1))
        raise RuntimeError("unreachable")


HTTP = Http()


# ---------------------------------------------------------------- helpers
def snippet(text: str, n: int = 200) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:n]


def save_raw(sid: str, content: bytes, ext: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{sid}.{ext}").write_bytes(content)


def freq_from_dates(dates: list[pd.Timestamp]) -> str | None:
    dates = sorted(set(pd.to_datetime(dates)))
    if len(dates) < 3:
        return None
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
    m = median(gaps)
    if m <= 1.5:
        return "daily"
    if m <= 8:
        return "weekly"
    if m <= 35:
        return "monthly"
    if m <= 100:
        return "quarterly"
    return "annual"


def classify_http(r: requests.Response, res: Result, original_url: str) -> None:
    res.http_status = r.status_code
    res.content_type = r.headers.get("Content-Type")
    res.last_modified = r.headers.get("Last-Modified")
    res.final_url = r.url
    code = r.status_code
    if code == 200:
        res.status = "OK"
        if urlparse(r.url).netloc.lower().removeprefix("www.") != urlparse(original_url).netloc.lower().removeprefix("www."):
            res.status = "MOVED"
            res.notes.append(f"redirected to another host: {r.url}")
        if re.search(r"/(login|signin|sign-in|account)\b", r.url, re.I):
            res.status = "LOGIN"
    elif code == 401:
        res.status = "LOGIN"
    elif code == 403:
        res.status = "BLOCKED"
        if "cf-ray" in r.headers or "cloudflare" in r.headers.get("Server", "").lower():
            res.notes.append("Cloudflare/WAF challenge — may need a real browser or manual download")
    elif code in (301, 302, 404, 410):
        res.status = "MOVED"
    else:
        res.status = "BLOCKED"


def check_robots(url: str, res: Result) -> None:
    p = urlparse(url)
    robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
    try:
        r = HTTP.get(robots_url)
        if r.status_code != 200:
            res.notes.append(f"robots.txt HTTP {r.status_code} (treated as allowed)")
            res.robots_allowed = True
            return
        rp = RobotFileParser()
        rp.parse(r.text.splitlines())
        res.robots_allowed = rp.can_fetch(UA, url)
        if not res.robots_allowed:
            res.notes.append("robots.txt disallows this path")
    except Exception as e:  # noqa: BLE001
        res.notes.append(f"robots.txt unreachable: {type(e).__name__}")


# ---------------------------------------------------------------- checkers
def _hdr(src: dict) -> dict:
    return {"User-Agent": BROWSER_UA} if src.get("ua") == "browser" else {}


def chk_http(src: dict, res: Result) -> None:
    r = HTTP.get(src["url"], headers=_hdr(src))
    if src.get("ua") == "browser":
        res.notes.append("browser User-Agent required (firewall rejects tool UA)")
    classify_http(r, res, src["url"])
    body = r.text if "text" in (res.content_type or "") or "html" in (res.content_type or "") else ""
    res.sample = snippet(body) if body else f"<{len(r.content)} bytes binary>"
    save_raw(res.id, r.content, "html" if body else "bin")
    if body:
        visible = snippet(body, 100000)
        if re.search(r"Request Rejected|Access Denied|Attention Required", visible[:300], re.I):
            res.status = "BLOCKED"
            res.notes.append("web firewall returned a 'Request Rejected' page to a scripted client — needs a real browser session or manual download")
        elif len(visible) < 300 or (len(visible) < 2000 and re.search(r"enable javascript|need to enable javascript", visible, re.I)):
            res.status = "BLOCKED" if res.status == "OK" else res.status
            res.notes.append("JS-only app (no data in HTML) — needs a headless browser or its underlying JSON endpoint; else MANUAL")
        if src.get("expect_text") and src["expect_text"].lower() not in body.lower():
            res.notes.append(f"expected text '{src['expect_text']}' NOT found")
            if res.status == "OK":
                res.status = "MOVED"
        elif src.get("expect_text"):
            res.notes.append(f"found '{src['expect_text']}'")
    if src.get("robots"):
        check_robots(src["url"], res)
        if res.robots_allowed is False and res.status == "OK":
            res.status = "BLOCKED"


def chk_rss(src: dict, res: Result) -> None:
    import feedparser

    r = HTTP.get(src["url"])
    classify_http(r, res, src["url"])
    if r.status_code != 200:
        return
    save_raw(res.id, r.content, "xml")
    feed = feedparser.parse(r.content)
    if not feed.entries:
        res.status = "MOVED"
        res.notes.append("no feed entries parsed (not an RSS/Atom feed?)")
        res.sample = snippet(r.text)
        return
    dates = []
    for e in feed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        if t:
            dates.append(datetime(*t[:6], tzinfo=timezone.utc))
    if dates:
        res.latest_obs = max(dates).astimezone(CAIRO).isoformat(timespec="minutes")
    res.frequency_observed = f"{len(feed.entries)} items in feed"
    res.sample = (feed.entries[0].get("title") or "")[:200]


def chk_fred_csv(src: dict, res: Result) -> None:
    rows, missing = [], []
    for sid in src["series_ids"]:
        url = f"{src['url']}?id={sid}"
        try:
            r = HTTP.get(url, gap=1.0)
        except Exception as e:  # noqa: BLE001
            missing.append(f"{sid}: {type(e).__name__}")
            continue
        if r.status_code != 200 or not r.text.lower().startswith(("observation_date", "date")):
            missing.append(f"{sid}: HTTP {r.status_code}")
            continue
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = ["date", "value"]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna()
        if df.empty:
            missing.append(f"{sid}: no numeric data")
            continue
        last = df.iloc[-1]
        rows.append(f"{sid}={last['date']} ({freq_from_dates(df['date'].tail(12).tolist())}, last={last['value']})")
    res.http_status = 200 if rows else None
    res.status = "OK" if rows and not missing else ("MOVED" if rows else "BLOCKED")
    res.latest_obs = "; ".join(rows)
    if missing:
        res.notes.append("problems: " + "; ".join(missing))
    res.notes.append("keyless fredgraph CSV works without an API key; API key only needed for metadata/vintages (ALFRED)")
    res.sample = rows[0] if rows else None


def chk_key_api(src: dict, res: Result) -> None:
    key = os.getenv(src["key_env"])
    res.needs_key = True
    if not key:
        res.status = "LOGIN"
        res.notes.append(f"free API key needed — set {src['key_env']} in .env (ASK before registering)")
        try:
            r = HTTP.get(src["url"])
            res.http_status = r.status_code
            res.sample = snippet(r.text)
        except Exception as e:  # noqa: BLE001
            res.notes.append(f"endpoint unreachable: {type(e).__name__}")
        return
    if src["kind"] == "fred_api":
        url = f"{src['url']}?series_id=DCOILBRENTEU&api_key={key}&file_type=json"
    else:
        url = f"{src['url']}petroleum/pri/spt/data/?api_key={key}&frequency=daily&data[0]=value&facets[series][]=RBRTE&sort[0][column]=period&sort[0][direction]=desc&length=1"
    r = HTTP.get(url)
    classify_http(r, res, url)
    res.final_url = src["url"]  # never write the key into reports
    res.sample = snippet(r.text.replace(key, "***"))


def chk_yfinance(src: dict, res: Result) -> None:
    import yfinance as yf

    rows, bad = [], []
    for t in src["tickers"]:
        try:
            h = yf.Ticker(t).history(period="1mo", auto_adjust=False)
        except Exception as e:  # noqa: BLE001
            bad.append(f"{t}: {type(e).__name__}")
            continue
        if h.empty:
            bad.append(f"{t}: empty")
            continue
        last = h.dropna(subset=["Close"]).iloc[-1]
        rows.append(f"{t}={h.index[-1].date()} close={last['Close']:.4g}")
        time.sleep(0.5)
    res.status = "OK" if rows and not bad else ("MOVED" if rows else "BLOCKED")
    res.http_status = 200 if rows else None
    res.latest_obs = "; ".join(rows)
    res.frequency_observed = "daily"
    res.notes.append("UNOFFICIAL source (Yahoo) — quality_flag='unofficial'")
    if bad:
        res.notes.append("problems: " + "; ".join(bad))


def chk_gpr_excel(src: dict, res: Result) -> None:
    r = HTTP.get(src["url"])
    classify_http(r, res, src["url"])
    if r.status_code != 200:
        return
    ext = src["url"].rsplit(".", 1)[-1]
    save_raw(res.id, r.content, ext)
    df = pd.read_excel(io.BytesIO(r.content))
    cols = [str(c) for c in df.columns]
    missing = [c for c in src.get("required_columns", []) if c not in cols]
    opt_found = [c for c in src.get("optional_columns", []) if c in cols]
    date_col = next((c for c in cols if c.lower() in ("month", "date", "day")), cols[0])
    col = df[date_col]
    if pd.api.types.is_numeric_dtype(col) and col.dropna().astype("int64").between(19000101, 21001231).all():
        dates = pd.to_datetime(col.dropna().astype("int64").astype(str), format="%Y%m%d", errors="coerce").dropna()
    else:
        dates = pd.to_datetime(col, errors="coerce").dropna()
    if not dates.empty:
        res.latest_obs = str(dates.max().date())
        res.frequency_observed = freq_from_dates(dates.tail(30).tolist())
    res.sample = f"{len(df)} rows, {len(cols)} columns; date column '{date_col}'"
    egy = [c for c in cols if "EGY" in c.upper()]
    if egy:
        res.notes.append(f"Egypt columns: {', '.join(egy)}")
        last_egy = df[[date_col, egy[0]]].dropna()
        if not last_egy.empty:
            res.notes.append(f"{egy[0]} latest non-null: {pd.to_datetime(last_egy[date_col].iloc[-1]).date()}")
    if opt_found:
        res.notes.append(f"optional columns present: {', '.join(opt_found)}")
    if missing:
        res.notes.append(f"MISSING required columns: {', '.join(missing)}")
        near = [c for c in cols if any(m.split('_')[0] in c for m in missing)][:15]
        res.notes.append(f"similar columns: {', '.join(near)}")
        res.status = "MOVED"


def chk_gdelt(src: dict, res: Result) -> None:
    r = HTTP.get(src["url"], gap=GDELT_GAP)
    classify_http(r, res, src["url"])
    save_raw(res.id, r.content, "json")
    try:
        data = r.json()
    except ValueError:
        res.status = "BLOCKED" if res.status == "OK" else res.status
        res.notes.append("non-JSON reply (rate limited or query error)")
        res.sample = snippet(r.text)
        return
    tl = data.get("timeline") or []
    pts = tl[0]["data"] if tl else []
    if not pts:
        res.notes.append("timeline empty")
        return
    dates = [pd.to_datetime(p["date"]) for p in pts]
    res.latest_obs = str(max(dates))
    res.frequency_observed = freq_from_dates(dates) or "sub-daily"
    res.sample = f"{tl[0].get('series')}: last value {pts[-1]['value']}"
    res.notes.append("rolling ~3-month window; keep >=6s between calls")


def chk_portwatch(src: dict, res: Result) -> None:
    search = HTTP.get(
        "https://www.arcgis.com/sharing/rest/search",
        params={"q": '"Daily Chokepoints Data" type:"Feature Service"', "f": "json", "num": 20},
    )
    items = [i for i in search.json().get("results", []) if i.get("url")]
    items.sort(key=lambda i: ("imf" not in (i.get("owner") or "").lower(), i.get("title") != "Daily_Chokepoints_Data"))
    if not items:
        res.status = "MOVED"
        res.notes.append("ArcGIS search found no 'Daily Chokepoints Data' feature service")
        return
    item = items[0]
    svc = item["url"].rstrip("/")
    layer = svc if re.search(r"/\d+$", svc) else f"{svc}/0"
    res.final_url = layer
    res.notes.append(f"ArcGIS item {item['id']} owner={item.get('owner')} title={item.get('title')}")

    meta = HTTP.get(layer, params={"f": "json"}).json()
    fields = [f["name"] for f in meta.get("fields", [])]
    res.notes.append(f"fields: {', '.join(fields[:25])}")
    id_f = next((f for f in fields if f.lower() == "portid"), None)
    name_f = next((f for f in fields if f.lower() == "portname"), None)
    date_f = next((f for f in fields if f.lower() == "date"), None)
    if not (id_f and name_f and date_f):
        res.status = "MOVED"
        res.notes.append("expected fields portid/portname/date not all present")
        return

    distinct = HTTP.get(f"{layer}/query", params={
        "where": "1=1", "outFields": f"{id_f},{name_f}", "returnDistinctValues": "true",
        "returnGeometry": "false", "f": "json"}).json()
    ids = {a["attributes"][name_f]: a["attributes"][id_f] for a in distinct.get("features", [])}
    want = src.get("expect_names", [])
    found = {n: pid for n, pid in ids.items() if any(w.lower().split()[0] in n.lower() for w in want)}
    res.notes.append(f"{len(ids)} chokepoints; matches: " + ", ".join(f"{n}={p}" for n, p in sorted(found.items())))
    if ids.get("Suez Canal") != src["expect_ids"]["suez"]:
        res.notes.append(f"WARNING Suez id is {ids.get('Suez Canal')!r}, expected {src['expect_ids']['suez']}")

    latest = HTTP.get(f"{layer}/query", params={
        "where": f"{id_f}='{src['expect_ids']['suez']}'", "outFields": "*", "orderByFields": f"{date_f} DESC",
        "resultRecordCount": 30, "returnGeometry": "false", "f": "json"}).json()
    feats = [f["attributes"] for f in latest.get("features", [])]
    res.http_status = 200
    if not feats:
        res.status = "MOVED"
        res.notes.append("no rows for Suez")
        return
    raw_dates = [a[date_f] for a in feats]
    dates = pd.to_datetime(raw_dates, unit="ms") if isinstance(raw_dates[0], (int, float)) else pd.to_datetime(raw_dates)
    res.latest_obs = str(max(dates).date())
    res.frequency_observed = freq_from_dates(list(dates))
    a = feats[0]
    res.sample = ", ".join(f"{k}={a[k]}" for k in list(a)[:10])
    res.status = "OK"
    save_raw(res.id, json.dumps(feats, default=str).encode(), "json")


def _latest_json(sid: str, data) -> str | None:
    try:
        if sid == "worldbank_api":
            obs = [d for d in data[1] if d.get("value") is not None]
            return f"{obs[0]['date']} value={obs[0]['value']:.2f}" if obs else None
        if sid == "imf_datamapper":
            vals = data["values"]["NGDP_RPCH"]["EGY"]
            return f"years {min(vals)}–{max(vals)} (includes WEO projections)"
        if sid == "ecb_hicp":
            per = data["structure"]["dimensions"]["observation"][0]["values"][-1]["id"]
            v = list(data["dataSets"][0]["series"].values())[0]["observations"]
            return f"{per} value={list(v.values())[-1][0]}"
        if sid == "eurostat_hicp":
            per = list(data["dimension"]["time"]["category"]["index"])[-1]
            return f"{per} value={list(data['value'].values())[-1]}"
    except Exception:  # noqa: BLE001
        return None
    return None


def chk_json(src: dict, res: Result) -> None:
    r = HTTP.get(src["url"], headers={"Accept": "application/json"})
    classify_http(r, res, src["url"])
    save_raw(res.id, r.content, "json")
    try:
        data = r.json()
    except ValueError:
        if res.status == "OK":
            res.status = "MOVED"
        res.notes.append("response is not JSON")
        res.sample = snippet(r.text)
        return
    res.sample = json.dumps(data, ensure_ascii=False)[:200]
    res.latest_obs = _latest_json(res.id, data)
    max_age = src.get("stale_after_days")
    if max_age and res.latest_obs:
        latest = pd.Period(res.latest_obs.split()[0]).end_time
        age = (pd.Timestamp.now() - latest).days
        if age > max_age:
            res.status = "MOVED"
            res.notes.append(f"STALE: latest period is {age} days old (> {max_age}) — series likely discontinued or renamed")


def chk_static(src: dict, res: Result) -> None:
    res.status = src["access"]  # MANUAL or PAID
    for k in ("notes", "manual_reason"):
        if src.get(k):
            res.notes.append(src[k])


def chk_cbe_api(src: dict, res: Result) -> None:
    r = HTTP.get(src["url"], headers=_hdr(src))
    classify_http(r, res, src["url"])
    data = r.json()
    items = data.get("results", [])
    res.sample = items[0]["title"][:200] if items else None
    res.latest_obs = items[0]["customDate"][:10] if items else None
    res.frequency_observed = f"{data.get('totalResultsCount')} news items (paged JSON)"
    nir = [i for i in items if "International Reserves" in i["title"]]
    if nir:
        res.notes.append(f"latest NIR headline: {nir[0]['title'][:120]}")


CHECKERS = {
    "http": chk_http, "rss": chk_rss, "fred_csv": chk_fred_csv, "fred_api": chk_key_api,
    "eia_api": chk_key_api, "yfinance": chk_yfinance, "gpr_excel": chk_gpr_excel,
    "gdelt": chk_gdelt, "portwatch": chk_portwatch, "json": chk_json,
    "manual": chk_static, "paid": chk_static, "cbe_api": chk_cbe_api,
}


# ---------------------------------------------------------------- report
def write_report(results: list[Result]) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "phase0_source_audit.json").write_text(
        json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False), encoding="utf-8")

    def cell(s) -> str:
        return str(s or "—").replace("|", "\\|").replace("\n", " ")

    now = datetime.now(CAIRO).strftime("%Y-%m-%d %H:%M")
    counts = pd.Series([r.status for r in results]).value_counts().to_dict()
    lines = [
        "# Phase 0 — Source audit",
        "",
        f"Run: {now} (Africa/Cairo). Status counts: " + ", ".join(f"**{k}** {v}" for k, v in counts.items()),
        "",
        "| source | status | HTTP | frequency observed | latest observation | notes |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        notes = r.notes.copy()
        if r.robots_allowed is not None:
            notes.insert(0, f"robots: {'allowed' if r.robots_allowed else 'DISALLOWED'}")
        notes = "; ".join(notes)
        lines.append(f"| `{r.id}` {cell(r.name)} | **{r.status}** | {cell(r.http_status)} | "
                     f"{cell(r.frequency_observed)} | {cell(r.latest_obs)} | {cell(notes)} |")
    lines += ["", "## Samples (first 200 chars)", ""]
    for r in results:
        lines.append(f"- `{r.id}` ({r.content_type or '—'}, last-modified {r.last_modified or '—'}): {cell(r.sample)}")
    path = REPORT_DIR / "phase0_source_audit.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    if load_dotenv:
        load_dotenv(ROOT / ".env")
    cfg = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text(encoding="utf-8"))
    sources = [s for s in cfg["sources"] if not argv or s["id"] in argv]
    results = []
    for i, src in enumerate(sources, 1):
        res = Result(id=src["id"], name=src["name"], access=src["access"])
        print(f"[{i:>2}/{len(sources)}] {src['id']:<24}", end=" ", flush=True)
        try:
            CHECKERS[src["kind"]](src, res)
        except Exception as e:  # noqa: BLE001
            res.status = "BLOCKED"
            res.notes.append(f"error: {type(e).__name__}: {str(e)[:150]}")
        if src["access"] in ("MANUAL", "PAID") and src["kind"] not in ("manual", "paid"):
            res.notes.insert(0, f"reachable={res.status}; policy keeps it {src['access']}")
            if src.get("manual_reason"):
                res.notes.append(src["manual_reason"])
            res.status = src["access"]
        print(res.status, "|", (res.latest_obs or "")[:70])
        results.append(res)
    path = write_report(results)
    print(f"\nAudit written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
