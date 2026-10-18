"""Live layer: intraday market quotes + live insights, refreshed every ~15 minutes (GitHub Actions).

Writes site/data/live.js. It never writes to the observations table: intraday quotes are delayed market
prices (quality 'unofficial'), kept apart from the official daily record. Every quote and insight carries
its source, URL and timestamp.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .core import CAIRO, SITE, get_logger, now_cairo
from .data import DataView
from .derive import gap_pct, gold_implied_fx

log = get_logger("pulse.live")

QUOTES = [  # id, yahoo symbol, EN name, AR name, unit, sign (+1 rise = pressure on EGP), digits
    ("usd_egp", "EGP=X", "USD/EGP (market)", "الدولار مقابل الجنيه (السوق)", "EGP", 1, 3),
    ("egx30", "^CASE30", "EGX30", "مؤشر البورصة إيجي إكس 30", "pts", 0, 0),
    ("brent", "BZ=F", "Brent oil", "بترول برنت", "$/bbl", 1, 2),
    ("gold", "GC=F", "Gold (world)", "الدهب العالمي", "$/oz", 0, 1),
    ("dxy", "DX-Y.NYB", "US dollar index", "مؤشر الدولار", "", 1, 2),
    ("vix", "^VIX", "VIX fear index", "مؤشر الخوف", "", 1, 2),
    ("us10y", "^TNX", "US 10-year yield", "عائد السندات الأمريكية 10 سنين", "%", 1, 3),
    ("wheat", "ZW=F", "Wheat", "القمح", "¢/bu", 1, 1),
    ("gas_eu", "TTF=F", "European gas (TTF)", "الغاز الأوروبي", "€/MWh", 1, 2),
    ("em_eq", "EEM", "Emerging-market stocks (EEM)", "أسهم الأسواق الناشئة", "$", -1, 2),
    ("cib", "COMI.CA", "CIB (Cairo)", "التجاري الدولي (القاهرة)", "EGP", 0, 2),
    ("cib_gdr", "CBKD.IL", "CIB GDR (London)", "التجاري الدولي (لندن)", "$", 0, 3),
]
YAHOO_URL = "https://finance.yahoo.com/quote/{}"
SPARK_POINTS = 60


def _bars(symbol: str):
    import yfinance as yf

    h = yf.Ticker(symbol).history(period="5d", interval="15m")
    return h.dropna(subset=["Close"]) if h is not None and not h.empty else None


def fetch_quotes() -> list[dict]:
    out = []
    now = datetime.now(timezone.utc)
    for qid, sym, en, ar, unit, sign, digits in QUOTES:
        try:
            h = _bars(sym)
        except Exception as e:  # noqa: BLE001
            log.warning("live quote %s failed: %s", sym, e)
            continue
        if h is None:
            continue
        last_ts = h.index[-1].to_pydatetime()
        last_day = h.index[-1].date()
        prev = h[[d.date() < last_day for d in h.index]]
        prev_close = float(prev["Close"].iloc[-1]) if not prev.empty else None
        price = float(h["Close"].iloc[-1])
        today = h[[d.date() == last_day for d in h.index]]
        age_min = (now - last_ts.astimezone(timezone.utc)).total_seconds() / 60
        out.append({
            "id": qid, "symbol": sym, "name_en": en, "name_ar": ar, "unit": unit, "sign": sign, "digits": digits,
            "price": round(price, 6), "prev_close": None if prev_close is None else round(prev_close, 6),
            "chg": None if prev_close is None else round(price - prev_close, 6),
            "chg_pct": None if not prev_close else round((price / prev_close - 1) * 100, 3),
            "ts": last_ts.astimezone(CAIRO).isoformat(timespec="minutes"), "open": age_min < 40,
            "spark": [[d.astimezone(CAIRO).isoformat(timespec="minutes"), round(float(v), 6)]
                      for d, v in zip(today.index[-SPARK_POINTS:], today["Close"].iloc[-SPARK_POINTS:])],
            "source": f"Yahoo Finance {sym} (delayed, unofficial)", "url": YAHOO_URL.format(sym.replace("^", "%5E")),
        })
    return out


def fetch_gold_eg() -> dict | None:
    from .collectors.cbe import page_text
    from .collectors.gold_eg import BANKLIVE, parse_banklive
    from .http import Http

    try:
        r = Http().get(BANKLIVE)
        p = parse_banklive(page_text(r.text))
    except Exception as e:  # noqa: BLE001
        log.warning("live gold failed: %s", e)
        return None
    if "gold_eg_21k" not in p or "xauusd_spot" not in p:
        return None
    ts = p.get("ts")
    return {"k21": p["gold_eg_21k"], "k24": p.get("gold_eg_24k"), "pound": p.get("gold_eg_pound"),
            "xau": p["xauusd_spot"], "ts": ts.replace(tzinfo=CAIRO).isoformat(timespec="minutes") if ts else None,
            "source": "banklive.net (Egypt gold, secondary)", "url": BANKLIVE}


def fetch_cbe_fx() -> dict | None:
    """Today's CBE official rate straight from the CBE page (published once each business morning)."""
    from .collectors.cbe import FX_PAGE, page_text
    from .http import Http

    try:
        t = page_text(Http(browser_ua=True).get(FX_PAGE).text)
        m = re.search(r"Average Market Rate in EGP\s+(\d{1,2} \w{3} \d{4}).*?US Dollar ([\d.]+) ([\d.]+)", t)
    except Exception as e:  # noqa: BLE001
        log.warning("live CBE FX failed: %s", e)
        return None
    if not m:
        return None
    d = datetime.strptime(m.group(1), "%d %b %Y").date()
    return {"buy": float(m.group(2)), "sell": float(m.group(3)), "date": d.isoformat(),
            "source": "Central Bank of Egypt — exchange rates", "url": FX_PAGE}


def fetch_news(limit: int = 12) -> list[dict]:
    import feedparser

    from .collectors.rss import feeds
    from .http import Http

    items = []
    http = Http(min_gap=0.5)
    for f in feeds():
        try:
            parsed = feedparser.parse(http.get(f["url"], retries=2).content)
        except Exception:  # noqa: BLE001
            continue
        for e in parsed.entries[:8]:
            t = e.get("published_parsed") or e.get("updated_parsed")
            when = datetime(*t[:6], tzinfo=timezone.utc).astimezone(CAIRO).isoformat(timespec="minutes") if t else None
            items.append({"title": e.get("title", "").strip(), "outlet": f.get("outlet", f["name"]), "url": e.get("link"),
                          "at": when})
    items = [i for i in items if i["title"] and i["url"]]
    items.sort(key=lambda i: i["at"] or "", reverse=True)
    return items[:limit]


def _pct(x) -> str:
    return "n/a" if x is None else f"{x:+.2f}%"


def _when(q, ar=False) -> str:
    """'today' while the market trades, else the date of the last session."""
    if q.get("open"):
        return "النهارده" if ar else "today"
    d = datetime.fromisoformat(q["ts"])
    return (f"في آخر جلسة {d:%d/%m}") if ar else f"in the last session, {d:%a %d %b}"


def _money(x: float) -> str:
    return f"{'+' if x >= 0 else '−'}${abs(x):.1f}"


def _q(quotes, qid):
    return next((q for q in quotes if q["id"] == qid), None)


def insights(quotes: list[dict], gold: dict | None, cbe: dict | None, v: DataView) -> list[dict]:
    """Plain-language live reads. Thresholds are tool defaults (same as the rule engine)."""
    out = []
    off = cbe["buy"] if cbe else (v.latest("fx_cbe_official").value if v.latest("fx_cbe_official") else None)
    off_src = cbe or {"source": "Central Bank of Egypt", "url": "https://www.cbe.org.eg/en/economic-research/statistics/exchange-rates"}

    def add(iid, d, en, ar, sources):
        out.append({"id": iid, "dir": d, "en": en, "ar": ar, "sources": sources})

    if gold and off:
        implied = gold_implied_fx(gold["k21"], gold["xau"])
        gap = gap_pct(implied, off)
        d = 1 if gap > 3 else (-1 if gap < -3 else 0)
        level = ("above +3%: people are paying a premium for gold — devaluation hedging" if gap > 3 else
                 "below −3%: local dollar demand is easing" if gap < -3 else "within the normal range (under ±3%) — no hidden pressure")
        level_ar = ("فوق 3%: الناس بتدفع زيادة في الدهب تحوط من التخفيض" if gap > 3 else
                    "تحت سالب 3%: الطلب على الدولار بيهدى" if gap < -3 else "جوه الحدود العادية، يعني مفيش ضغط مستخبي")
        add("gold_gap", d, f"Gold-implied dollar rate is {implied:.2f} vs the CBE official {off:.2f} → gap {gap:+.2f}%, {level}.",
            f"دولار الدهب {implied:.2f} جنيه مقابل الرسمي {off:.2f}، والفرق {gap:+.2f}%، {level_ar}.",
            [{"name": gold["source"], "url": gold["url"], "at": gold["ts"]}, {"name": off_src["source"], "url": off_src["url"]}])
    m = _q(quotes, "usd_egp")
    if m and off:
        g = gap_pct(m["price"], off)
        d = 1 if g > 1 else 0
        add("market_gap", d, f"Market USD/EGP {m['price']:.3f} vs official {off:.2f} ({g:+.2f}%)" +
            (" — the market is pricing a weaker pound." if g > 1 else " — in line with the official rate."),
            f"سعر الدولار في السوق العالمي {m['price']:.3f} مقابل الرسمي {off:.2f} بفرق {g:+.2f}%" +
            ("، والسوق متوقع ضعف الجنيه." if g > 1 else "، ومتماشي مع السعر الرسمي."),
            [{"name": m["source"], "url": m["url"], "at": m["ts"]}, {"name": off_src["source"], "url": off_src["url"]}])
    b = _q(quotes, "brent")
    bud = v.latest("budget_oil_assumption")
    if b and bud:
        gap = b["price"] - bud.value
        ca = 0.03 * gap
        d = 1 if gap > 10 else (-1 if gap < -10 else 0)
        add("oil_gap", d, f"Brent ${b['price']:.2f} ({_pct(b['chg_pct'])} {_when(b)}) is {_money(gap)} vs the ${bud.value:.0f} budget price"
            f" → about {ca:+.1f}% of GDP on the current account (IMF rule of thumb), plus pressure on fuel subsidies.",
            f"برنت {b['price']:.2f} دولار ({_pct(b['chg_pct'])} {_when(b, True)})، يعني {gap:+.1f} دولار عن سعر الموازنة،"
            f" وده ضغط حوالي {ca:+.1f}% من الناتج على الحساب الجاري وعلى دعم الوقود.",
            [{"name": b["source"], "url": b["url"], "at": b["ts"]}, {"name": bud.source_name, "url": bud.source_url}])
    e = _q(quotes, "egx30")
    if e and e.get("chg_pct") is not None:
        usd_note, usd_ar = "", ""
        if m and m.get("chg_pct") is not None:
            usd = ((1 + e["chg_pct"] / 100) / (1 + m["chg_pct"] / 100) - 1) * 100
            usd_note = f" In dollar terms {usd:+.2f}%."
            usd_ar = f" وبالدولار {usd:+.2f}%."
        add("egx", 0 if abs(e["chg_pct"]) < 1.5 else (-1 if e["chg_pct"] > 0 else 1),
            f"EGX30 {e['price']:,.0f} ({e['chg_pct']:+.2f}% {_when(e)}).{usd_note}",
            f"البورصة إيجي إكس 30 عند {e['price']:,.0f} نقطة ({e['chg_pct']:+.2f}% {_when(e, True)}).{usd_ar}",
            [{"name": e["source"], "url": e["url"], "at": e["ts"]}])
    vx, dx = _q(quotes, "vix"), _q(quotes, "dxy")
    if vx:
        risk_off = vx["price"] > 25
        dtxt = f" Dollar index {_pct(dx['chg_pct'])} {_when(dx)}." if dx and dx.get("chg_pct") is not None else ""
        add("risk", 1 if risk_off else 0,
            f"Global mood: VIX {vx['price']:.1f} — " + ("risk-off (above 25): money tends to leave emerging markets like Egypt." if risk_off
                                                       else "calm (below 25).") + dtxt,
            f"مزاج الأسواق العالمية: مؤشر الخوف {vx['price']:.1f}، " + ("المستثمرين خايفين والفلوس بتخرج من الأسواق الناشئة." if risk_off
                                                                      else "الأسواق هادية."),
            [{"name": vx["source"], "url": vx["url"], "at": vx["ts"]}] + ([{"name": dx["source"], "url": dx["url"], "at": dx["ts"]}] if dx else []))
    cl, cg = _q(quotes, "cib"), _q(quotes, "cib_gdr")
    if cl and cg and off and cg["price"]:
        imp = cl["price"] / cg["price"]
        prem = gap_pct(imp, off)
        hist = v.series("cib_gdr_premium_pct")
        base = float(hist.iloc[-60:].mean()) if len(hist) >= 20 else None
        dev = None if base is None else prem - base
        d = 1 if (dev is not None and dev > 3) else (-1 if (dev is not None and dev < -3) else 0)
        btxt = f" Its recent average is {base:+.1f}%, so today's reading is {dev:+.1f} pp from normal." if base is not None else ""
        add("hot_money", d, f"Hot-money gauge: CIB in Cairo ÷ CIB in London implies {imp:.2f} EGP/$ — {prem:+.1f}% vs official.{btxt} "
            "A widening gap means foreign investors price a weaker pound.",
            f"مؤشر الأموال الساخنة: سعر سهم التجاري الدولي في القاهرة على سعره في لندن بيدي دولار بـ {imp:.2f} جنيه، "
            f"يعني فرق {prem:+.1f}% عن الرسمي. لو الفرق بيوسع يبقى الأجانب متوقعين ضعف الجنيه.",
            [{"name": cl["source"], "url": cl["url"], "at": cl["ts"]}, {"name": cg["source"], "url": cg["url"], "at": cg["ts"]}])
    gw = _q(quotes, "gold")
    if gw and gw.get("chg_pct") is not None and abs(gw["chg_pct"]) >= 0.5:
        add("gold_world", 0, f"World gold {gw['chg_pct']:+.2f}% {_when(gw)} (${gw['price']:,.0f}) — moves local gold prices and the value of the CBE's gold reserves.",
            f"الدهب العالمي {gw['chg_pct']:+.2f}% {_when(gw, True)}، وده بيحرك سعر الدهب المحلي وقيمة دهب البنك المركزي.",
            [{"name": gw["source"], "url": gw["url"], "at": gw["ts"]}])
    return out


def load_prev(src: str | None) -> dict:
    if not src:
        return {}
    try:
        if src.startswith("http"):
            import requests
            txt = requests.get(src, params={"t": datetime.now().timestamp()}, timeout=20).text
        else:
            p = Path(src)
            txt = p.read_text(encoding="utf-8") if p.exists() else ""
        m = re.search(r"window\.__pulseLive\((.*)\);\s*$", txt, re.S)
        return json.loads(m.group(1)) if m else {}
    except Exception as e:  # noqa: BLE001
        log.warning("previous live.js not loaded (%s) — starting fresh history", e)
        return {}


def build_live(conn, prev_src: str | None = None) -> dict:
    v = DataView(conn)
    quotes = fetch_quotes()
    gold = fetch_gold_eg()
    cbe = fetch_cbe_fx()
    news = fetch_news()
    ins = insights(quotes, gold, cbe, v)
    now = now_cairo()
    # rolling intraday history of the key live reads (kept across runs via the previously published file)
    prev = load_prev(prev_src)
    hist = prev.get("hist", {}) if isinstance(prev, dict) else {}
    cutoff = (now - timedelta(days=3)).isoformat(timespec="minutes")
    stamp = now.isoformat(timespec="minutes")
    for key, val in (("gold_implied", gold_implied_fx(gold["k21"], gold["xau"]) if gold else None),
                     ("gold_21k", gold["k21"] if gold else None)):
        if val is None:
            continue
        pts = [p for p in hist.get(key, []) if p[0] >= cutoff]
        if not pts or pts[-1][1] != round(val, 4):
            pts.append([stamp, round(val, 4)])
        hist[key] = pts[-300:]
    return {"generated": now.isoformat(timespec="seconds"), "quotes": quotes, "gold_eg": gold, "cbe": cbe,
            "insights": ins, "news": news, "hist": hist,
            "note": "Intraday prices are delayed market quotes (unofficial) refreshed about every 15 minutes; "
                    "official figures update when the source publishes."}


def write_live(conn, prev_src: str | None = None) -> str:
    payload = build_live(conn, prev_src)
    out = SITE / "data"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "live.js"
    path.write_text("window.__pulseLive(" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str) + ");\n",
                    encoding="utf-8")
    log.info("live: %d quotes, gold=%s, cbe=%s, %d insights, %d headlines", len(payload["quotes"]),
             bool(payload["gold_eg"]), bool(payload["cbe"]), len(payload["insights"]), len(payload["news"]))
    return str(path)
