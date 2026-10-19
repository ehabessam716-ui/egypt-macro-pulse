"""Central Bank of Egypt (cbe.org.eg).

The site's firewall rejects non-browser User-Agents, so these requests use ctx.browser (standard
browser UA, >= 2.5 s between requests). robots.txt allows every path used here.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup

from ..core import get_logger, today_cairo
from ..db import add_obs, save_raw
from ..news import store_news
from . import collector

log = get_logger("pulse.cbe")
B = "https://www.cbe.org.eg"
SRC = "Central Bank of Egypt"
FX_PAGE = B + "/en/economic-research/statistics/exchange-rates"
FX_HIST = FX_PAGE + "/historical-data"
CPI_PAGE = B + "/en/economic-research/statistics/inflation-rates"
TB_PAGE = B + "/en/auctions/egp-t-bills"
TB_HIST = TB_PAGE + "/historical-data"
MPC_PAGE = B + "/en/monetary-policy/mpc-meetings-schedule"
CONIA_PAGE = B + "/en/economic-research/statistics/conia"
NEWS_API = B + "/api/listing/News"
NEWS_DS = "{DE996AEC-03FB-4E24-BDB0-EF64F75FD5AD}"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
     "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
           "ten": 10, "eleven": 11, "twelve": 12, "first": 1}


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for x in soup(["script", "style", "nav", "header", "footer"]):
        x.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def month_year(s: str) -> date | None:
    m = re.match(r"\s*([A-Za-z]+)\.?\s+(\d{4})", s)
    if not m or m.group(1).lower() not in MONTHS:
        return None
    return date(int(m.group(2)), MONTHS[m.group(1).lower()], 1)


def dmy(s: str) -> date:
    return datetime.strptime(s.strip(), "%d/%m/%Y").date()


def _num(s) -> float:
    return float(str(s).replace(",", "").replace("%", "").strip())


def historical(ctx, page_url: str, frm: date, to: date, extra: dict | None = None) -> str:
    """CBE 'View Historical Data' form: GET page for the anti-forgery token, then POST the API."""
    r = ctx.browser.get(page_url)
    form = BeautifulSoup(r.text, "lxml").find("form", id="historicalDataForm")
    if form is None:
        raise RuntimeError(f"historical form not found on {page_url}")
    data = {i["name"]: i.get("value", "") for i in form.find_all("input")
            if i.get("name") and i.get("type") != "radio"}
    data.update(extra or {})
    data.update(FromDateRaw=frm.strftime("%d/%m/%Y"), ToDateRaw=to.strftime("%d/%m/%Y"), SubmitAction="1")
    r = ctx.browser.post(B + "/api/statistics/GetHistoricalData", data=data,
                         headers={"X-Requested-With": "XMLHttpRequest", "Referer": page_url})
    return r.text


# ---------------------------------------------------------------- FX
@collector("cbe_fx")
def collect_fx(conn, ctx) -> int:
    backfill = ctx.backfill or not ctx.has_rows(conn, "fx_cbe_official")
    frm = date(2023, 1, 1) if backfill else today_cairo() - timedelta(days=30)
    rows = 0
    try:
        html = historical(ctx, FX_HIST, frm, today_cairo(), {"SelectedSelectOptions": "US Dollar"})
        save_raw(conn, "cbe_fx_hist", FX_HIST, html.encode("utf-8"), "html")
        df = pd.read_html(io.StringIO(html))[0]
        df = df[df["Currency"].astype(str).str.contains("US Dollar")]
        for d, buy, sell in zip(df["Date"], df["Buy"], df["Sell"]):
            od = dmy(str(d))
            for sid, v in (("fx_cbe_official", buy), ("fx_cbe_official_sell", sell)):
                res = add_obs(conn, sid, od, _num(v), unit="EGP per USD", source_name=SRC + " — exchange rates",
                              source_url=FX_HIST, quality_flag="official", release_date=od)
                rows += res != "same"
        return rows
    except Exception as e:  # noqa: BLE001 — fall back to today's page
        log.warning("CBE FX history failed (%s); using the current rates page", e)
    r = ctx.browser.get(FX_PAGE)
    save_raw(conn, "cbe_fx", FX_PAGE, r.content, "html")
    t = page_text(r.text)
    m = re.search(r"Average Market Rate in EGP\s+(\d{1,2} \w{3} \d{4}).*?US Dollar ([\d.]+) ([\d.]+)", t)
    if not m:
        raise RuntimeError("USD row not found on CBE exchange-rate page")
    od = datetime.strptime(m.group(1), "%d %b %Y").date()
    for sid, v in (("fx_cbe_official", m.group(2)), ("fx_cbe_official_sell", m.group(3))):
        rows += add_obs(conn, sid, od, float(v), unit="EGP per USD", source_name=SRC + " — exchange rates",
                        source_url=FX_PAGE, quality_flag="official", release_date=od) != "same"
    return rows


# ---------------------------------------------------------------- key rates + CONIA
@collector("cbe_rates")
def collect_rates(conn, ctx) -> int:
    rows = 0
    r = ctx.browser.get(MPC_PAGE)
    save_raw(conn, "cbe_mpc", MPC_PAGE, r.content, "html")
    t = page_text(r.text)
    eff = re.search(r"Effective from (\d{1,2})(?:st|nd|rd|th)? of ([A-Za-z]+) (\d{4})", t)
    if not eff:
        raise RuntimeError("effective date not found on MPC page")
    od = date(int(eff.group(3)), MONTHS[eff.group(2).lower()], int(eff.group(1)))
    found = 0
    for sid, label in (("cbe_odr", "Overnight Deposit Rate"), ("cbe_olr", "Overnight Lending Rate"),
                       ("cbe_mainop", "MAIN OPERATION"), ("cbe_discount", "Discount Rates?")):
        m = re.search(label + r"\s+(\d{1,2}\.\d{1,3})\s*%", t, re.I)
        if m:
            found += 1
            rows += add_obs(conn, sid, od, float(m.group(1)), unit="%", source_name=SRC + " — key CBE rates",
                            source_url=MPC_PAGE, quality_flag="official",
                            obs_note="obs_date = 'effective from' date on the CBE page") != "same"
    if found < 4:
        log.warning("only %s of 4 key rates parsed from the MPC page", found)
    # CONIA: dated table on its statistics page
    try:
        r = ctx.browser.get(CONIA_PAGE)
        save_raw(conn, "cbe_conia", CONIA_PAGE, r.content, "html")
        rows += _parse_conia(conn, r.text)
    except Exception as e:  # noqa: BLE001
        log.warning("CONIA page: %s", e)
    return rows


def _parse_conia(conn, html: str) -> int:
    rows = 0
    try:
        tables = pd.read_html(io.StringIO(html))
    except ValueError:
        tables = []
    for tb in tables:
        cols = [str(c).lower() for c in tb.columns]
        dcol = next((c for c in tb.columns if "date" in str(c).lower()), None)
        vcol = next((c for c in tb.columns if "conia" in str(c).lower() or "rate" in str(c).lower()), None)
        if dcol is None or vcol is None:
            continue
        for d, v in zip(tb[dcol], tb[vcol]):
            try:
                od = pd.to_datetime(str(d), dayfirst=True).date()
                val = _num(v)
            except Exception:  # noqa: BLE001
                continue
            rows += add_obs(conn, "interbank_overnight", od, val, unit="%", source_name=SRC + " — CONIA",
                            source_url=CONIA_PAGE, quality_flag="official", release_date=od) != "same"
        if cols:
            break
    if rows == 0:
        t = page_text(html)
        m = re.search(r"(\d{1,2} [A-Za-z]{3} \d{4})[^%]{0,80}?(\d{1,2}\.\d{2,4})\s*%", t)
        if m and "CONIA" in t:
            od = datetime.strptime(m.group(1), "%d %b %Y").date()
            rows += add_obs(conn, "interbank_overnight", od, float(m.group(2)), unit="%",
                            source_name=SRC + " — CONIA", source_url=CONIA_PAGE, quality_flag="official",
                            release_date=od) != "same"
    return rows


# ---------------------------------------------------------------- CPI page (latest month)
CPI_LABELS = {"headline (m/m)": "cpi_urban_mom", "core (m/m)": "cpi_core_mom", "headline (y/y)": "cpi_urban_yoy",
              "core (y/y)": "cpi_core_yoy", "regulated items (m/m)": "cpi_regulated_mom",
              "fruits and vegetables (m/m)": "cpi_fv_mom", "regulated items (y/y)": "cpi_regulated_yoy",
              "fruits and vegetables (y/y)": "cpi_fv_yoy"}


def parse_cpi_page(text: str) -> tuple[date, date | None, dict[str, float]]:
    m = re.search(r"Inflation for Last Month:\s*([A-Za-z]{3,9} \d{4})\s+(.*?)\s+((?:-?\d+\.\d+%\s*)+)", text)
    if not m:
        raise RuntimeError("CPI block not found")
    month = month_year(m.group(1))
    labels = re.findall(r"[A-Za-z][A-Za-z ]*?\((?:m/m|y/y)\)", m.group(2))
    values = [float(v) for v in re.findall(r"-?\d+\.\d+", m.group(3))]
    rel = re.search(r"Last Updated:\s*(\d{1,2} [A-Za-z]{3} \d{4})", text)
    release = datetime.strptime(rel.group(1), "%d %b %Y").date() if rel else None
    out = {}
    for lab, val in zip(labels, values):
        sid = CPI_LABELS.get(lab.strip().lower())
        if sid:
            out[sid] = val
    return month, release, out


@collector("cbe_cpi")
def collect_cpi(conn, ctx) -> int:
    r = ctx.browser.get(CPI_PAGE)
    save_raw(conn, "cbe_cpi", CPI_PAGE, r.content, "html")
    month, release, vals = parse_cpi_page(page_text(r.text))
    if not vals:
        raise RuntimeError("no CPI values parsed")
    rows = 0
    for sid, v in vals.items():
        rows += add_obs(conn, sid, month, v, unit="%", source_name=SRC + " — inflation rates",
                        source_url=CPI_PAGE, quality_flag="official", release_date=release) != "same"
    return rows


# ---------------------------------------------------------------- T-bill auctions
TENOR_KEY = {91: "3m", 182: "6m", 273: "9m", 357: "12m", 364: "12m"}


@collector("cbe_auctions")
def collect_auctions(conn, ctx) -> int:
    backfill = ctx.backfill or not ctx.has_rows(conn, "tbill_3m_yield")
    frm = today_cairo() - timedelta(days=1100 if backfill else 60)
    html = historical(ctx, TB_HIST, frm, today_cairo())
    save_raw(conn, "cbe_tbills_hist", TB_HIST, html.encode("utf-8"), "html")
    tables = pd.read_html(io.StringIO(html))
    best: dict[tuple[str, date], dict] = {}
    for tb in tables:
        if "Tenor (days)" not in tb.columns:
            continue
        for rec in tb.to_dict("records"):
            try:
                key = TENOR_KEY.get(int(rec["Tenor (days)"]))
                od = dmy(str(rec["Issue Date"]))
                req, sub, acc = _num(rec["Required Amount"]), _num(rec["Submitted Amount"]), _num(rec["Accepted Amount"])
                y = _num(rec["Weighted Avg. Yield (%)"])
            except (ValueError, KeyError, TypeError):
                continue
            if not key or req <= 0:
                continue
            k = (key, od)
            if k not in best or acc > best[k]["acc"]:
                best[k] = {"y": y, "req": req, "sub": sub, "acc": acc, "isin": rec.get("ISIN"),
                           "n": (best[k]["n"] + 1) if k in best else 1}
            else:
                best[k]["n"] += 1
    rows = 0
    for (key, od), b in best.items():
        note = f"ISIN {b['isin']}; obs_date = issue date"
        if b["n"] > 1:
            note += f"; {b['n']} auctions this issue date — the one with the largest accepted amount is shown"
        rows += add_obs(conn, f"tbill_{key}_yield", od, b["y"], unit="%", source_name=SRC + " — T-bill auctions",
                        source_url=TB_HIST, quality_flag="official", release_date=od, obs_note=note) != "same"
        rows += add_obs(conn, f"tbill_{key}_btc", od, round(b["sub"] / b["req"], 4), unit="ratio",
                        source_name=SRC + " — T-bill auctions (submitted/required)", source_url=TB_HIST,
                        quality_flag="derived", release_date=od, obs_note=note) != "same"
        rows += add_obs(conn, f"tbill_{key}_accepted_ratio", od, round(b["acc"] / b["req"], 4), unit="ratio",
                        source_name=SRC + " — T-bill auctions (accepted/required)", source_url=TB_HIST,
                        quality_flag="derived", release_date=od, obs_note=note) != "same"
    return rows


# ---------------------------------------------------------------- news listing + press releases
def _news_items(ctx, pages: int, page_size: int) -> list[dict]:
    items = []
    for p in range(pages):
        r = ctx.browser.get(NEWS_API, params={"pageNo": p, "pageSize": page_size, "datasourceItemId": NEWS_DS})
        res = r.json().get("results", [])
        items += res
        if len(res) < page_size:
            break
    return items


def _processed(conn, url: str) -> bool:
    return conn.execute("SELECT 1 FROM raw_files WHERE url=? AND source LIKE 'cbe_pr_%'", (url,)).fetchone() is not None


NIR_RE = re.compile(r"Net International Reserves[^$]*?US\s?\$\s*([\d,]+(?:\.\d+)?)\s*(mn|million|bn|billion)\s+(?:at|by)\s+(?:the\s+)?end\s+of\s+([A-Za-z]+),?\s+(\d{4})", re.I)


def parse_nir_title(title: str) -> tuple[date, float] | None:
    m = NIR_RE.search(title)
    if not m or m.group(3).lower() not in MONTHS:
        return None
    v = _num(m.group(1))
    if m.group(2).lower() in ("bn", "billion"):
        v *= 1000
    return date(int(m.group(4)), MONTHS[m.group(3).lower()], 1), v


def parse_cpi_release(text: str) -> list[tuple[str, date, float]]:
    """CBE CPI press release: sentences with 'X percent in <Month YYYY>' pairs."""
    out = []
    for sent in re.split(r"(?<=\.)\s+(?=[A-Z])", text):
        s = sent.lower()
        if "percent in" not in s:
            continue
        if "core" in s:
            kind = "core"
        elif "headline" in s and "urban" in s:
            kind = "urban"
        else:
            continue
        head = s[: s.find("percent in")]
        mi, ai = head.rfind("monthly"), max(head.rfind("annual"), head.rfind("year-on-year"))
        if mi < 0 and ai < 0:
            continue
        freq = "mom" if mi > ai else "yoy"
        # CBE writes negatives in words: "negative 0.5 percent" (also handle "minus" and a leading sign)
        for neg, v, mon in re.findall(r"((?:negative|minus)\s+)?(-?\d+(?:\.\d+)?) percent in ([A-Z][a-z]+ \d{4})", sent, re.I):
            d = month_year(mon)
            if d:
                val = float(v)
                out.append((f"cpi_{kind}_{freq}", d, -abs(val) if neg else val))
    return out


def parse_remittances(text: str) -> list[tuple[str, date, float, str | None]]:
    out = []
    m = re.search(r"remittances[^.]*?(rose|increased|grew|jumped|surged|declined|decreased|fell|dropped)\s+by\s+"
                  r"([\d.]+)\s?(?:%|percent)\s+in\s+([A-Z][a-z]+ \d{4}),?\s+(?:recording|registering|to record|"
                  r"to register|reaching|to reach)\s+(?:about |around |nearly |some )?(?:USD|US\$)\s*([\d.]+)\s+billion"
                  r"\s*\((?:against|compared (?:to|with))\s+(?:about |around |nearly )?(?:USD|US\$)\s*([\d.]+)\s+billion"
                  r"\s+in\s+([A-Z][a-z]+ \d{4})\)", text, re.I)
    if m:
        sign = -1 if m.group(1).lower() in ("declined", "decreased", "fell", "dropped") else 1
        d, d0 = month_year(m.group(3)), month_year(m.group(6))
        if d:
            out.append(("remittances", d, float(m.group(4)), None))
            out.append(("remittances_yoy", d, sign * float(m.group(2)), None))
        if d0:
            out.append(("remittances", d0, float(m.group(5)), None))
    m = re.search(r"first (\w+) months of (\d{4})", text, re.I)
    v = re.search(r"(?:inflows|record(?:ing)?|register(?:ing)?)[^.(]{0,60}?(?:USD|US\$)\s*([\d.]+)\s+billion\s*\("
                  r"(?:compared (?:to|with)|against)\s+(?:about |around )?(?:USD|US\$)\s*([\d.]+)\s+billion", text, re.I)
    if m and v and m.group(1).lower() in WORDNUM:
        n, yr = WORDNUM[m.group(1).lower()], int(m.group(2))
        note = f"January–{date(yr, n, 1):%B} cumulative"
        out.append(("remittances_ytd", date(yr, n, 1), float(v.group(1)), note))
        out.append(("remittances_ytd", date(yr - 1, n, 1), float(v.group(2)), note))
    return out


HAWK = ["tighten", "tightening", "upside risk", "inflationary pressure", "elevated", "restrictive", "vigilant",
        "hike", "raise", "accelerat", "persist", "second-round", "cautious"]
DOVE = ["easing", "ease", "cut", "moderat", "declin", "downside", "disinflation", "slowdown", "subdued",
        "accommodative", "reduce", "support economic activity", "below its potential"]


def parse_mpc(text: str) -> dict:
    out: dict = {}
    t = text
    if re.search(r"decided to (keep|maintain|hold)", t, re.I):
        out["decision"] = 0
    elif re.search(r"decided to (cut|reduce|lower)", t, re.I):
        out["decision"] = -1
    elif re.search(r"decided to (raise|hike|increase)", t, re.I):
        out["decision"] = 1
    else:  # e.g. "decided in an unscheduled meeting held on March 16, 2020 to cut ..."
        m = re.search(r"decided\b[^.]{0,140}?\bto (raise|hike|increase|cut|reduce|lower|keep|maintain|hold)\b", t, re.I)
        if m:
            w = m.group(1).lower()
            out["decision"] = 1 if w in ("raise", "hike", "increase") else -1 if w in ("cut", "reduce", "lower") else 0
    for sent in re.split(r"(?<=\.)\s+(?=[A-Z])", t):
        if "overnight deposit rate" in sent.lower() and "main operation" in sent.lower():
            vals = [float(v) for v in re.findall(r"(\d{1,2}\.\d{1,2}) percent", sent)]
            if len(vals) >= 3:
                out["cbe_odr"], out["cbe_olr"], out["cbe_mainop"] = vals[-3:]
                break
    m = re.search(r"discount rate[^.]{0,80}?(\d{1,2}\.\d{1,2}) percent", t, re.I)
    if m:
        out["cbe_discount"] = float(m.group(1))
    q = re.search(r"growth recording ([\d.]+) percent in Q([1-4]) (\d{4})(?:, (?:down|up) from ([\d.]+) percent in Q([1-4]) (\d{4}))?", t)
    if q:
        out["gdp_q"] = [(date(int(q.group(3)), 3 * int(q.group(2)) - 2, 1), float(q.group(1)))]
        if q.group(4):
            out["gdp_q"].append((date(int(q.group(6)), 3 * int(q.group(5)) - 2, 1), float(q.group(4))))
    fy = re.search(r"real GDP growth averaged ([\d.]+) percent in FY ?(\d{4})/(\d{2,4})", t)
    if fy:
        out["gdp_fy"] = (date(int(fy.group(2)), 7, 1), float(fy.group(1)))
    words = max(len(t.split()), 1)
    low = t.lower()
    hawk = sum(low.count(w) for w in HAWK)
    dove = sum(low.count(w) for w in DOVE)
    out["tone"] = round((hawk - dove) / words * 1000, 2)
    out["tone_counts"] = (hawk, dove, words)
    return out


BOP_ITEMS = [
    # (series, label regex, sign) — value read from the first "US$ X billion (against US$ Y billion)" after the label
    ("imports_nonoil_fy", r"Non-oil merchandise import payments", 1),
    ("exports_nonoil_fy", r"non-oil merchandise export proceeds", 1),
    ("imports_oil_fy", r"(?<![Nn]on-)\bOil imports", 1),
    ("exports_oil_fy", r"(?<![Nn]on-)\boil exports (?:increased|decreased|rose|fell|went)", 1),
    ("trade_nonoil_balance_fy", r"non-oil trade deficit", -1),
    ("trade_oil_balance_fy", r"(?<![Nn]on-)\boil trade deficit", -1),
    ("invest_income_balance_fy", r"Investment income deficit", -1),
    ("remittances_fy", r"Remittances of Egyptians working abroad (?:surged|rose|increased|declined|fell)", 1),
    ("tourism_receipts_fy", r"Tourism revenues (?:rose|increased|declined|fell|surged)", 1),
    ("suez_receipts_fy", r"Suez Canal transit receipts", 1),
    ("fdi_net_fy", r"FDI in Egypt (?:recorded|witnessed|registered) a net inflow", 1),
    ("capital_financial_net_fy", r"capital and financial account (?:registered|witnessed|recorded)", 1),
]
VAL_RE = re.compile(r"US\$\s*([\d.]+)\s+billion(?:[^(.]{0,60}?\((?:against|compared with)\s+(?:an? [a-z ]+? of )?US\$\s*([\d.]+)\s+billion\))?")


def _sentence_after(t: str, pos: int, limit: int = 420) -> str:
    w = t[pos: pos + limit]
    w = w.split("•")[0]
    m = re.search(r"\.\s+[A-Z]", w)
    return w[: m.start() + 1] if m else w


def parse_bop(text: str) -> tuple[int | None, list[tuple[str, date, float]]]:
    t = re.sub(r"\s+", " ", text)
    fy = re.search(r"During FY ?(\d{4})/(\d{2,4})", t)
    if not fy:
        return None, []
    y = int(fy.group(1))
    cur, prev = date(y, 7, 1), date(y - 1, 7, 1)
    out: list[tuple[str, date, float]] = []

    def put(sid, sign, m):
        out.append((sid, cur, sign * float(m.group(1))))
        if m.group(2):
            out.append((sid, prev, sign * float(m.group(2))))

    m = re.search(r"overall (surplus|deficit) of US\$ ([\d.]+) billion \(against an overall (surplus|deficit) of US\$ ([\d.]+) billion\)", t)
    if m:
        out.append(("bop_overall_fy", cur, (1 if m.group(1) == "surplus" else -1) * float(m.group(2))))
        out.append(("bop_overall_fy", prev, (1 if m.group(3) == "surplus" else -1) * float(m.group(4))))
    m = re.search(r"current account recorded a (deficit|surplus) of US\$ ([\d.]+) billion[^(]{0,60}\(against US\$ ([\d.]+) billion\)", t)
    if m:
        s = -1 if m.group(1) == "deficit" else 1
        out += [("bop_ca_fy", cur, s * float(m.group(2))), ("bop_ca_fy", prev, s * float(m.group(3)))]
    m = re.search(r"merchandise trade balance by [\d.]+ percent to reach US\$ ([\d.]+) billion", t)
    if m:
        out.append(("trade_balance_fy", cur, -float(m.group(1))))
    m = re.search(r"services surplus by [\d.]+ percent to record US\$ ([\d.]+) billion", t)
    if m:
        out.append(("services_surplus_fy", cur, float(m.group(1))))
    m = re.search(r"portfolio investments? in Egypt recorded a net (inflow|outflow) of US\$ ([\d.]+) billion", t)
    if m:
        out.append(("portfolio_net_fy", cur, (1 if m.group(1) == "inflow" else -1) * float(m.group(2))))
    for sid, label, sign in BOP_ITEMS:
        first_any = None
        chosen = None
        for lm in re.finditer(label, t):
            cands = list(VAL_RE.finditer(_sentence_after(t, lm.end())))
            with_prev = next((m for m in cands if m.group(2)), None)
            if with_prev:
                chosen = with_prev
                break
            if cands and first_any is None:
                first_any = cands[-1] if len(cands) > 1 and re.search(r"by US\$", _sentence_after(t, lm.end())) else cands[0]
        chosen = chosen or first_any
        if chosen:
            put(sid, sign, chosen)
    return y, out


@collector("cbe_news")
def collect_news(conn, ctx) -> int:
    backfill = ctx.backfill or not ctx.has_rows(conn, "nir")
    items = _news_items(ctx, pages=10 if backfill else 1, page_size=100 if backfill else 40)
    horizon = today_cairo() - timedelta(days=3 * 365 if backfill else 120)
    rows = 0
    for it in items:
        title = it.get("title") or ""
        if not it.get("customDate") or not it.get("url"):
            continue
        d = datetime.fromisoformat(it["customDate"][:19]).date()
        url = B + it["url"]
        cats = {c.get("value") for c in (it.get("categories") or []) if isinstance(c, dict)}
        store_news(conn, "Central Bank of Egypt", url, title, None, it["customDate"])
        nir = parse_nir_title(title)
        if nir:
            rows += add_obs(conn, "nir", nir[0], nir[1], unit="USD mn", source_name=SRC + " — NIR press release",
                            source_url=url, quality_flag="official", release_date=d,
                            obs_note="provisional" if "rovisional" in title else None) != "same"
            continue
        if d < horizon:
            continue
        kind = None
        if "MPC Press Release" in cats or title.startswith("MPC Press Release"):
            kind = "mpc"
        elif "CPI Press Release" in cats or "Inflation Data" in title or title.startswith("CPI Press Release"):
            kind = "cpi"
        elif "Remittances" in cats or "Remittances" in title:
            kind = "remit"
        elif "Balance of Payments" in cats or "Balance of Payments" in title or "BOP" in title:
            kind = "bop"
        if not kind or _processed(conn, url):
            continue
        try:
            rows += _process_release(conn, ctx, kind, url, d)
            conn.commit()
        except Exception as e:  # noqa: BLE001
            log.warning("CBE %s release %s: %s", kind, url, e)
    return rows


def _process_release(conn, ctx, kind: str, url: str, d: date) -> int:
    r = ctx.browser.get(url)
    text = page_text(r.text)
    rows = 0
    if kind == "cpi":
        for sid, od, v in parse_cpi_release(text):
            rows += add_obs(conn, sid, od, v, unit="%", source_name=SRC + " — CPI press release", source_url=url,
                            quality_flag="official", release_date=d) != "same"
    elif kind == "remit":
        for sid, od, v, note in parse_remittances(text):
            unit = "%" if sid.endswith("yoy") else "USD bn"
            rows += add_obs(conn, sid, od, v, unit=unit, source_name=SRC + " — remittances press release",
                            source_url=url, quality_flag="official", release_date=d, obs_note=note) != "same"
    elif kind == "mpc":
        p = parse_mpc(text)
        for sid in ("cbe_odr", "cbe_olr", "cbe_mainop", "cbe_discount"):
            if sid in p:
                rows += add_obs(conn, sid, d, p[sid], unit="%", source_name=SRC + " — MPC press release",
                                source_url=url, quality_flag="official", release_date=d,
                                obs_note="obs_date = MPC decision date") != "same"
        if "decision" in p:
            rows += add_obs(conn, "cbe_mpc_decision", d, p["decision"], unit="code",
                            source_name=SRC + " — MPC press release", source_url=url, quality_flag="official",
                            release_date=d) != "same"
        h, dv, w = p["tone_counts"]
        rows += add_obs(conn, "cbe_mpc_tone", d, p["tone"], unit="score", source_name=SRC + " — MPC statement (tone)",
                        source_url=url, quality_flag="derived", release_date=d,
                        obs_note=f"hawkish words {h}, dovish words {dv}, total words {w} — tool heuristic") != "same"
        for od, v in p.get("gdp_q", []):
            rows += add_obs(conn, "gdp_growth", od, v, unit="%", source_name=SRC + " — MPC press release",
                            source_url=url, quality_flag="official", release_date=d,
                            obs_note="quarterly real GDP growth y/y as quoted by the MPC") != "same"
        if "gdp_fy" in p:
            rows += add_obs(conn, "gdp_growth_fy", p["gdp_fy"][0], p["gdp_fy"][1], unit="%",
                            source_name=SRC + " — MPC press release", source_url=url, quality_flag="official",
                            release_date=d) != "same"
    elif kind == "bop":
        soup = BeautifulSoup(r.text, "lxml")
        pdf = next((a["href"] for a in soup.find_all("a", href=True) if a["href"].lower().endswith(".pdf")
                    and "bop" in a["href"].lower()), None)
        if pdf:
            import pdfplumber

            pr = ctx.browser.get(B + pdf if pdf.startswith("/") else pdf)
            save_raw(conn, "cbe_bop_pdf", pr.url, pr.content, "pdf")
            with pdfplumber.open(io.BytesIO(pr.content)) as doc:
                text = "\n".join(pg.extract_text() or "" for pg in doc.pages)
            src_url = pr.url
        else:
            src_url = url
        fy, vals = parse_bop(text)
        if fy is None:
            log.info("BoP release %s is not a fiscal-year release; quarterly parsing not supported (skipped)", url)
        for sid, od, v in vals:
            rows += add_obs(conn, sid, od, v, unit="USD bn", source_name=SRC + " — BoP press release",
                            source_url=src_url, quality_flag="official", release_date=d,
                            obs_note=f"fiscal year {od.year}/{str(od.year + 1)[-2:]} (Jul–Jun)") != "same"
    save_raw(conn, f"cbe_pr_{kind}", url, r.content, "html")
    return rows


def reparse_saved(conn) -> int:
    """Re-run parsers over press releases already cached in data/raw (no network)."""
    rows = 0
    for r in conn.execute("SELECT url, outlet, title, published_at FROM news_items WHERE outlet='Central Bank of Egypt'").fetchall():
        nir = parse_nir_title(r["title"])
        if nir:
            rows += add_obs(conn, "nir", nir[0], nir[1], unit="USD mn", source_name=SRC + " — NIR press release",
                            source_url=r["url"], quality_flag="official", release_date=r["published_at"][:10],
                            obs_note="provisional" if "rovisional" in r["title"] else None) != "same"
    for r in conn.execute("SELECT url, path FROM raw_files WHERE source='cbe_pr_cpi'").fetchall():
        try:
            text = page_text(open(r["path"], encoding="utf-8", errors="replace").read())
        except OSError:
            continue
        rel = conn.execute("SELECT published_at FROM news_items WHERE url=?", (r["url"],)).fetchone()
        for sid, od, v in parse_cpi_release(text):
            rows += add_obs(conn, sid, od, v, unit="%", source_name=SRC + " — CPI press release", source_url=r["url"],
                            quality_flag="official", release_date=rel[0][:10] if rel else None) != "same"
    return rows


@collector("cbe_mpc_hist")
def collect_mpc_history(conn, ctx) -> int:
    """Every MPC decision since 2005 from the CBE's own press releases (raise / keep / cut + overnight deposit rate).
    Used to show how the CBE reacted after past dollar jumps. Only releases not yet parsed are fetched."""
    import pdfplumber

    rows = 0
    done = {r[0] for r in conn.execute("SELECT obs_date FROM observations WHERE series_id='cbe_mpc_decision'")}
    items = conn.execute("SELECT substr(published_at,1,10), url, title FROM news_items WHERE outlet='Central Bank of Egypt' "
                         "AND (title LIKE '%MPC%' OR title LIKE '%interest rate%' OR title LIKE '%exchange rate regime%' OR title LIKE '%liberaliz%') "
                         "AND title NOT LIKE '%Report%' AND title NOT LIKE '%scheduled%' AND title NOT LIKE '%Date Change%' "
                         "AND title NOT LIKE '%Reschedul%' ORDER BY published_at").fetchall()
    for d, url, title in items:
        if d in done or not url:
            continue
        try:
            r = ctx.browser.get(url)
            if url.lower().endswith(".pdf") or r.content[:4] == b"%PDF":
                with pdfplumber.open(io.BytesIO(r.content)) as doc:
                    text = " ".join((p.extract_text() or "") for p in doc.pages[:3])
            else:
                text = page_text(r.text)
        except Exception as e:  # noqa: BLE001
            log.warning("MPC %s failed: %s", url, e)
            continue
        p = parse_mpc(re.sub(r"\s+", " ", text))
        if "decision" not in p and "cbe_odr" in p:  # fall back to the rate change vs the previous meeting
            prev = conn.execute("SELECT value FROM observations WHERE series_id='cbe_odr' AND obs_date<? ORDER BY obs_date DESC LIMIT 1", (d,)).fetchone()
            if prev:
                p["decision"] = 1 if p["cbe_odr"] > prev[0] + 1e-9 else -1 if p["cbe_odr"] < prev[0] - 1e-9 else 0
        if "decision" not in p:
            continue
        rows += add_obs(conn, "cbe_mpc_decision", d, p["decision"], unit="code", source_name="Central Bank of Egypt — MPC press release",
                        source_url=url, quality_flag="official", obs_note="+1 raise, 0 hold, -1 cut") != "same"
        if "cbe_odr" in p:
            rows += add_obs(conn, "cbe_odr", d, p["cbe_odr"], unit="%", source_name="Central Bank of Egypt — MPC press release",
                            source_url=url, quality_flag="official") != "same"
        conn.commit()
    return rows
