"""Yahoo Finance via yfinance — market proxies, always quality_flag='unofficial'."""
from __future__ import annotations

import time

from ..data import catalog
from ..db import add_obs
from . import collector


def ticker_map() -> dict[str, str]:
    return {m["endpoint"]: sid for sid, m in catalog().items() if m.get("source") == "yahoo_markets"}


@collector("yahoo")
def collect(conn, ctx) -> int:
    import yfinance as yf

    rows, errors = 0, []
    for tkr, sid in ticker_map().items():
        period = "5y" if (ctx.backfill or not ctx.has_rows(conn, sid)) else "3mo"
        try:
            h = yf.Ticker(tkr).history(period=period, auto_adjust=False)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{tkr}: {type(e).__name__}")
            continue
        if h is None or h.empty:
            errors.append(f"{tkr}: empty")
            continue
        h = h.dropna(subset=["Close"])
        note = "daily close as reported by Yahoo"
        if len(h) <= 5:  # e.g. ^CASE30: Yahoo serves no daily history — use hourly bars
            try:
                hh = yf.Ticker(tkr).history(period="730d", interval="1h").dropna(subset=["Close"])
                if len(hh) > len(h):
                    h = hh.groupby(hh.index.date).tail(1)
                    note = "daily close = last hourly bar of the day (Yahoo has no daily history for this symbol)"
            except Exception:  # noqa: BLE001
                pass
        unit = catalog()[sid].get("unit")
        for idx, close in zip(h.index, h["Close"]):
            res = add_obs(conn, sid, idx.date(), float(close), unit=unit,
                          source_name=f"Yahoo Finance {tkr} (unofficial)",
                          source_url=f"https://finance.yahoo.com/quote/{tkr}", quality_flag="unofficial",
                          obs_note=note)
            rows += res in ("new", "revised", "conflict")
        time.sleep(0.5)
    if errors and rows == 0 and len(errors) == len(ticker_map()):
        raise RuntimeError("; ".join(errors))
    return rows
