"""Economist-style data audit: plausibility ranges, accounting identities, cross-source checks, jumps.

`pulse audit` writes reports/data_audit.md and returns a summary that the web app shows on the Data page.
Checks never change data; they flag it (and the tests pin the parser fixes they led to).
"""
from __future__ import annotations

import math
from datetime import timedelta

import numpy as np
import pandas as pd

from .core import REPORTS, now_cairo, today_cairo
from .data import DataView, catalog

# plausible ranges for Egypt / global data (outside = almost certainly a parsing or unit error)
RANGES = {
    "fx_cbe_official": (5, 200), "fx_market": (5, 200), "fx_gold_implied": (5, 250), "cib_gdr_implied_fx": (5, 300),
    "cbe_odr": (0, 40), "cbe_olr": (0, 40), "cbe_mainop": (0, 40), "interbank_overnight": (0, 45),
    "cpi_urban_yoy": (-5, 60), "cpi_core_yoy": (-5, 60), "cpi_urban_mom": (-5, 15), "cpi_core_mom": (-5, 15),
    "nir": (5_000, 120_000), "pmi": (25, 70), "saudi_pmi": (25, 70), "uae_pmi": (25, 70),
    "tbill_3m_yield": (2, 40), "tbill_12m_yield": (2, 40), "tbill_12m_btc": (0.1, 15), "remittances": (0.5, 8),
    "remittances_yoy": (-80, 200), "brent": (5, 250), "brent_fut": (-50, 250), "xauusd": (200, 10_000),
    "gold_eg_21k": (100, 30_000), "egx30": (1_000, 200_000), "gdp_growth": (-15, 15), "vix": (5, 90),
    "us10y": (0, 15), "fed_funds": (0, 15), "suez_ratio_7dma": (0, 2), "hormuz_ratio_7dma": (0, 2),
}


def _row(status: str, check: str, detail: str) -> dict:
    return {"status": status, "check": check, "detail": detail}


def run_audit(conn) -> dict:
    v = DataView(conn)
    res: list[dict] = []

    # 1) plausible ranges
    bad = []
    for sid, (lo, hi) in RANGES.items():
        s = v.series(sid)
        out = s[(s < lo) | (s > hi)]
        if len(out):
            bad.append(f"{sid}: {len(out)} value(s) outside [{lo}, {hi}], e.g. {out.index[0].date()}={out.iloc[0]:g}")
    res.append(_row("fail" if bad else "pass", "Plausible ranges (" + str(len(RANGES)) + " series)",
                    "; ".join(bad) if bad else "all values inside expected ranges"))

    # 2) CPI identity: (1+yoy_t)/(1+yoy_t-1) = (1+mom_t)/(1+mom_t-12)
    mism, n = [], 0
    yo, mo = v.series("cpi_urban_yoy"), v.series("cpi_urban_mom")
    for d in yo.index:
        d1, d12 = d - pd.DateOffset(months=1), d - pd.DateOffset(months=12)
        if d1 in yo.index and d in mo.index and d12 in mo.index:
            n += 1
            lhs = (1 + yo[d] / 100) / (1 + yo[d1] / 100)
            rhs = (1 + mo[d] / 100) / (1 + mo[d12] / 100)
            if abs(lhs - rhs) > 0.004:
                mism.append(f"{d:%b %Y}")
    res.append(_row("fail" if mism else "pass", f"CPI identity yearly vs monthly ({n} months testable)",
                    ("inconsistent: " + ", ".join(mism)) if mism else "every testable month is consistent (rounding ±0.4pp)"))

    # 3) policy corridor order
    c = pd.concat([v.series("cbe_odr"), v.series("cbe_mainop"), v.series("cbe_olr")], axis=1, keys=["odr", "main", "olr"], sort=True).dropna()
    viol = c[(c.odr > c.main) | (c.main > c.olr)]
    res.append(_row("fail" if len(viol) else "pass", "Interest-rate corridor deposit ≤ main ≤ lending",
                    f"{len(viol)} violation(s)" if len(viol) else f"{len(c)} MPC observations in order"))

    # 4) BoP identity: trade balance = oil + non-oil balances (FY)
    tb, oil, non = v.series("trade_balance_fy"), v.series("trade_oil_balance_fy"), v.series("trade_nonoil_balance_fy")
    errs = [f"{d.year}/{str(d.year + 1)[-2:]}: {tb[d]:g} vs {oil[d] + non[d]:g}" for d in tb.index
            if d in oil.index and d in non.index and abs(tb[d] - (oil[d] + non[d])) > 0.25]
    res.append(_row("fail" if errs else "pass", "BoP: trade balance = oil + non-oil",
                    "; ".join(errs) if errs else "consistent (within rounding)"))

    # 5) NIR = FX + gold + SDR (when the breakdown exists)
    nir, g, fx, sdr = v.series("nir"), v.series("nir_gold"), v.series("nir_fx"), v.series("nir_sdr")
    errs = [f"{d:%b %Y}: {nir[d]:,.1f} vs {g[d] + fx[d] + sdr[d]:,.1f}" for d in nir.index
            if d in g.index and d in fx.index and d in sdr.index and abs(nir[d] - (g[d] + fx[d] + sdr[d])) > 10]
    res.append(_row("fail" if errs else "pass", "Reserves = FX + gold + SDR", "; ".join(errs) if errs else "consistent"))

    # 6) cross-source: official vs market vs gold-implied (latest)
    off, mk, gi = v.latest("fx_cbe_official"), v.latest("fx_market"), v.latest("fx_gold_implied")
    if off and mk and gi:
        gm, gg = (mk.value / off.value - 1) * 100, (gi.value / off.value - 1) * 100
        status = "warn" if abs(gm) > 2 or abs(gg) > 5 else "pass"
        res.append(_row(status, "Dollar rate: official vs market vs gold-implied",
                        f"market {gm:+.2f}%, gold-implied {gg:+.2f}% vs official {off.value:.4f} ({off.date})"))

    # 7) Brent: dated spot vs futures
    sp = v.latest("brent_spot_premium_pct")
    if sp:
        res.append(_row("warn" if abs(sp.value) > 8 else "pass", "Brent: dated spot vs benchmark futures",
                        f"spot premium {sp.value:+.1f}% on {sp.date} — the budget comparison uses benchmark futures; "
                        "a wide premium signals a physical supply squeeze (or a source issue worth watching)"))

    # 8) CIB London vs Cairo premium regime
    cp = v.series("cib_gdr_premium_pct")
    if len(cp) > 60:
        res.append(_row("pass", "CIB London-implied rate vs official",
                        f"latest {cp.iloc[-1]:+.1f}% vs 60-session average {cp.iloc[-60:].mean():+.1f}% "
                        "(structural gap ~15% in 2024–25 from GDR conversion limits; read the change)"))

    # 9) suspicious jumps (single-day moves beyond what the series has ever done around known events)
    jumps = []
    for sid, lim in (("fx_cbe_official", 10), ("nir", 25), ("gold_eg_21k", 12), ("egx30", 12), ("brent_fut", 25), ("xauusd", 12)):
        s = v.series(sid)
        if len(s) < 3:
            continue
        r = (s.pct_change() * 100)
        if catalog()[sid]["frequency"] == "monthly":  # only consecutive months (gaps would look like jumps)
            prev = s.index.to_series().shift(1)
            consecutive = (s.index.to_period("M") - prev.dt.to_period("M")).map(lambda x: getattr(x, "n", None)) == 1
            r = r[consecutive.values]
        r = r.dropna()
        big = r[r.abs() > lim]
        for d, x in big.tail(3).items():
            jumps.append(f"{sid} {d.date()} {x:+.1f}%")
    known = {"fx_cbe_official 2024-03-06"}  # March 2024 float — a real event
    unexplained = [j for j in jumps if " ".join(j.split()[:2]) not in known]
    res.append(_row("warn" if unexplained else "pass", "One-day jumps beyond normal",
                    ("check: " + ", ".join(unexplained)) if unexplained else "only known events (e.g. the March 2024 float)"))

    # 10) freshness of automatic sources
    stale = []
    for sid, m in catalog().items():
        if m["access"] in ("MANUAL", "PAID", "DERIVED"):
            continue
        o = v.latest(sid)
        if o is None:
            stale.append(f"{sid} (no data)")
        elif o.stale == 2:
            stale.append(f"{sid} ({o.date})")
    res.append(_row("warn" if stale else "pass", "Automatic sources fresh",
                    ("very stale / empty: " + ", ".join(stale)) if stale else "all automatic series within their freshness window"))

    # 11) seeds vs primary
    from .core import load_yaml
    diffs = []
    for s_ in load_yaml("seeds.yaml").get("observations", []):
        row = conn.execute("""SELECT value FROM observations WHERE series_id=? AND obs_date=? AND quality_flag='official'
                              ORDER BY vintage DESC LIMIT 1""", (s_["series_id"], str(s_["obs_date"]))).fetchone()
        if row and abs(row[0] - s_["value"]) > max(0.005 * abs(s_["value"]), 0.051):
            diffs.append(f"{s_['series_id']} {s_['obs_date']}: seed {s_['value']} vs official {row[0]}")
    res.append(_row("warn" if diffs else "pass", "Spec seeds vs primary sources", "; ".join(diffs) if diffs else "no conflicts"))

    counts = {k: sum(r["status"] == k for r in res) for k in ("pass", "warn", "fail")}
    summary = {"generated": now_cairo().isoformat(timespec="minutes"), "counts": counts, "checks": res}
    lines = [f"# Data audit — {today_cairo()}", "", f"{counts['pass']} pass · {counts['warn']} to watch · {counts['fail']} fail", "",
             "| status | check | detail |", "|---|---|---|"]
    lines += [f"| {r['status'].upper()} | {r['check']} | {r['detail']} |" for r in res]
    lines += ["", "## Fixes made from earlier audits", "",
              "- CPI m/m: the CBE writes negatives in words ('negative 0.5 percent'); the parser dropped the word, so 4 deflation",
              "  months were stored as positive (May 2024, Jun 2025, Jul 2025, Jun 2026). Fixed + re-parsed + unit test.",
              "- Brent: dated spot (EIA) ran 19–25% above benchmark futures in Oct 2026. The daily oil-vs-budget signal used spot while",
              "  the live layer used futures. Both now use benchmark futures; the spot premium is tracked as its own indicator."]
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "data_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
