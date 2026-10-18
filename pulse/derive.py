"""Derived metrics (SPEC §5). Pure formulas first (unit-tested), then history builders.

Every derived value is stored with quality_flag='derived' and an obs_note naming its inputs, their
sources and dates. A derived value is only computed when every input exists — nothing is filled in.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .core import DERIVED_SOURCE, get_logger, period_end
from .data import DataView
from .db import add_obs

log = get_logger("pulse.derive")
TROY_OZ_G = 31.1035
PURITY = {"21k": 0.875, "24k": 0.999}
MISMATCH_HOURS = 6


# ------------------------------------------------------------------ pure formulas
def real_rate(policy_rate: float, inflation: float) -> float:
    return policy_rate - inflation


def gold_implied_fx(local_egp_per_gram: float, xau_usd_per_oz: float, karat: str = "21k") -> float:
    return local_egp_per_gram / (xau_usd_per_oz / TROY_OZ_G * PURITY[karat])


def gap_pct(a: float, b: float) -> float:
    return (a / b - 1.0) * 100.0


def local_premium_egp(local_21k: float, xau: float, fx_official: float) -> float:
    return local_21k - (xau / TROY_OZ_G * PURITY["21k"] * fx_official)


def pmi_implied_gdp(pmi: float) -> float:
    return pmi * 0.269 - 8.62


def ca_pressure_pct_gdp(brent_gap: float) -> float:
    """IMF rule of thumb: +$10/bbl ≈ +0.3% of GDP on the current-account deficit."""
    return 0.03 * brent_gap


def pct_change(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0


def realized_vol(values: list[float], periods_per_year: int = 250) -> float:
    r = np.diff(np.log(np.asarray(values, dtype=float)))
    return float(np.std(r, ddof=1) * math.sqrt(periods_per_year) * 100.0)


def eda_signal(fx_chg_pct: float, cpi_index_chg_pct: float, odr_chg_pct: float) -> float:
    """Reconstruction of EDA Decision 480/2026 weights as reported in press (60/30/10)."""
    return 0.6 * fx_chg_pct + 0.3 * cpi_index_chg_pct + 0.1 * odr_chg_pct


def cumulative_from_mom(mom_pcts: list[float]) -> float:
    return (float(np.prod([1 + m / 100.0 for m in mom_pcts])) - 1.0) * 100.0


def carry_ex_post(tbill_3m_yield: float, fx_chg_3m_pct: float) -> float:
    return tbill_3m_yield / 4.0 - fx_chg_3m_pct


def carry_ex_ante(tbill_12m_yield: float, expected_depreciation_pct: float) -> float:
    return tbill_12m_yield - expected_depreciation_pct


# ------------------------------------------------------------------ storage helper
class Writer:
    def __init__(self, conn):
        self.conn = conn
        self.n = 0
        self.counts: dict[str, int] = {}

    def put(self, sid: str, d, value: float | None, unit: str, formula: str, inputs: str) -> None:
        if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
            return
        res = add_obs(self.conn, sid, d, round(float(value), 6), unit=unit, source_name=DERIVED_SOURCE,
                      source_url=f"pulse/derive.py#{formula}", quality_flag="derived", obs_note=inputs[:900])
        if res != "same":
            self.n += 1
            self.counts[sid] = self.counts.get(sid, 0) + 1


def _cite(o) -> str:
    return f"{o.series_id}={o.value:g} ({o.source_name}, {o.date})"


# ------------------------------------------------------------------ builders
def build_real_rates(v: DataView, w: Writer) -> None:
    for sid_cpi, out, policy in (("cpi_urban_yoy", "real_headline", "cbe_odr"), ("cpi_core_yoy", "real_core", "cbe_odr"),
                                 ("cpi_urban_yoy", "real_ceiling", "cbe_olr")):
        for d, cpi in v.series(sid_cpi).items():
            pe = period_end(d.date(), "monthly")
            p = v.value_at(policy, pe)
            if p is None:
                continue
            w.put(out, d.date(), real_rate(p.value, cpi), "pp", out,
                  f"{_cite(p)} − {sid_cpi}={cpi:g} ({d.date():%b %Y})")
    # real_expected: policy − CBE projected inflation in force at that month
    for d, _ in v.series("cpi_urban_yoy").items():
        pe = period_end(d.date(), "monthly")
        p, e = v.value_at("cbe_odr", pe), v.value_at("infl_expectations", pe)
        if p and e:
            w.put("real_expected", d.date(), real_rate(p.value, e.value), "pp", "real_expected", f"{_cite(p)} − {_cite(e)}")
    # also at each forecast date: deposit rate in force then minus the new forecast
    for d, ev in v.series("infl_expectations").items():
        p = v.value_at("cbe_odr", d.date())
        e = v.value_at("infl_expectations", d.date())
        if p and e:
            w.put("real_expected", d.date(), real_rate(p.value, ev), "pp", "real_expected", f"{_cite(p)} − {_cite(e)}")


def build_gold(v: DataView, w: Writer) -> None:
    gold = v.frame("gold_eg_21k")
    for r in gold.itertuples():
        d = r.obs_date
        spot = v.frame("xauusd_spot")
        spot = spot[spot["obs_date"] == d]
        note_t = ""
        if not spot.empty:
            xau, xsrc = float(spot["value"].iloc[-1]), f"xauusd_spot={spot['value'].iloc[-1]:g} ({spot['source_name'].iloc[-1]}, {d})"
        else:
            fut = v.value_at("xauusd", d)
            if fut is None or (d - fut.date).days > 3:
                continue
            xau, xsrc = fut.value, _cite(fut)
            note_t = "; WARNING timestamp mismatch > 6h (local scrape vs futures daily close)"
        implied = gold_implied_fx(float(r.value), xau)
        ins = f"gold_eg_21k={r.value:g} ({r.source_name}, {d} {r.obs_time or ''}); {xsrc}{note_t}"
        w.put("fx_gold_implied", d, implied, "EGP per USD", "gold_implied_fx", ins)
        off = v.value_at("fx_cbe_official", d)
        if off is not None and (d - off.date).days <= 4:
            gap_note = "" if off.date == d else f"; official rate in force from {off.date} (CBE closed {d:%a})"
            w.put("gold_gap_pct", d, gap_pct(implied, off.value), "%", "gap_pct", f"{ins}; {_cite(off)}{gap_note}")
            prem = local_premium_egp(float(r.value), xau, off.value)
            w.put("gold_local_premium_egp", d, prem, "EGP/gram", "local_premium_egp", f"{ins}; {_cite(off)}")
            fair = float(r.value) - prem
            w.put("gold_local_premium_pct", d, prem / fair * 100.0, "%", "local_premium_egp", f"{ins}; {_cite(off)}")


def build_fx(v: DataView, w: Writer) -> None:
    s = v.series("fx_cbe_official")
    if s.empty:
        return
    vals, idx = s.values, s.index
    for i in range(len(s)):
        d = idx[i].date()
        src = "fx_cbe_official (Central Bank of Egypt)"
        for lag, sid in ((1, "fx_chg_1d"), (5, "fx_chg_5d"), (20, "fx_chg_20d")):
            if i - lag >= 0:
                w.put(sid, d, pct_change(vals[i], vals[i - lag]), "%", "pct_change",
                      f"{src}: {vals[i]:g} on {d} vs {vals[i - lag]:g} on {idx[i - lag].date()} ({lag} CBE business days)")
        if i >= 20:
            w.put("fx_vol_20d", d, realized_vol(list(vals[i - 20:i + 1])), "%", "realized_vol",
                  f"{src}: 20 daily log returns to {d}, ×√250")
        back = s[s.index <= idx[i] - pd.Timedelta(days=91)]
        if not back.empty and (idx[i] - back.index[-1]).days <= 98:
            w.put("fx_chg_3m", d, pct_change(vals[i], back.iloc[-1]), "%", "pct_change",
                  f"{src}: {vals[i]:g} on {d} vs {back.iloc[-1]:g} on {back.index[-1].date()}")
            t3 = v.value_at("tbill_3m_yield", back.index[-1].date())
            if t3 is not None and (back.index[-1].date() - t3.date).days <= 14:
                w.put("carry_ex_post_3m", d, carry_ex_post(t3.value, pct_change(vals[i], back.iloc[-1])), "%",
                      "carry_ex_post", f"{_cite(t3)} /4 − USD/EGP change {back.index[-1].date()}→{d}")
    m = v.series("fx_market")
    for d, val in m.items():
        if d in s.index:
            w.put("fx_market_gap_pct", d.date(), gap_pct(val, s[d]), "%", "gap_pct",
                  f"fx_market={val:g} (Yahoo EGP=X, unofficial) vs fx_cbe_official={s[d]:g} (CBE), {d.date()}")
    # ex-ante carry on gold-gap dates
    for d, g in v.series("gold_gap_pct").items():
        t12 = v.value_at("tbill_12m_yield", d.date())
        if t12 is not None and (d.date() - t12.date).days <= 21:
            w.put("carry_ex_ante", d.date(), carry_ex_ante(t12.value, g), "%", "carry_ex_ante",
                  f"{_cite(t12)} − gold_gap_pct={g:.2f} (expected depreciation proxy, {d.date()})")


def _brent_daily(v: DataView) -> tuple[pd.Series, str]:
    """Benchmark Brent for the budget comparison: front-month futures (the price the press, the MoF and
    markets quote). Falls back to EIA dated spot where no futures close exists. The spot-vs-futures premium
    is tracked separately (brent_spot_premium_pct)."""
    fut, spot = v.series("brent_fut"), v.series("brent")
    if fut.empty:
        return spot, "brent (FRED DCOILBRENTEU, EIA spot)"
    extra = spot[spot.index > fut.index[-1]]
    return pd.concat([fut, extra]).sort_index(), "brent_fut (Yahoo BZ=F, benchmark futures)"


def build_energy(v: DataView, w: Writer) -> None:
    b, main_src = _brent_daily(v)
    fut_idx = set(v.series("brent_fut").index)
    for d, price in b.items():
        dd = d.date()
        src = main_src if d in fut_idx or not fut_idx else "brent (FRED DCOILBRENTEU, EIA spot — no futures close that day)"
        bud = v.value_at("budget_oil_assumption", dd)
        if bud is not None:
            gap = price - bud.value
            w.put("brent_gap", dd, gap, "USD/bbl", "brent_gap", f"{src}={price:g} on {dd} − {_cite(bud)}")
            w.put("ca_pressure_pct_gdp", dd, ca_pressure_pct_gdp(gap), "% GDP", "ca_pressure_pct_gdp",
                  f"IMF rule of thumb 0.03 × brent_gap ({gap:.2f}); {src} on {dd}")
        fx = v.value_at("fx_cbe_official", dd)
        if fx is not None and (dd - fx.date).days <= 4:
            w.put("brent_egp", dd, price * fx.value, "EGP/bbl", "brent_egp", f"{src}={price:g} on {dd} × {_cite(fx)}")


def build_brent_spread(v: DataView, w: Writer) -> None:
    spot, fut = v.series("brent"), v.series("brent_fut")
    for d, sp in spot.items():
        if d in fut.index and fut[d]:
            w.put("brent_spot_premium_pct", d.date(), gap_pct(sp, fut[d]), "%", "gap_pct",
                  f"brent spot {sp:g} (FRED DCOILBRENTEU, EIA) vs brent_fut {fut[d]:g} (Yahoo BZ=F), {d.date()}")


def build_brent_quarter(v: DataView, w: Writer) -> None:
    be = v.series("brent_egp")
    if be.empty:
        return
    q = be.index.to_period("Q")
    qavg = be.groupby(q).mean()
    for d, _ in be.items():
        cur = d.to_period("Q")
        prev = cur - 1
        if prev in qavg.index:
            cur_avg = be[(q == cur) & (be.index <= d)].mean()
            w.put("brent_egp_qavg_chg", d.date(), pct_change(cur_avg, qavg[prev]), "%", "pct_change",
                  f"avg brent_egp {cur} to date ({cur_avg:,.0f}) vs {prev} avg ({qavg[prev]:,.0f})")


def build_external(v: DataView, w: Writer) -> None:
    nir = v.series("nir")
    for d, val in nir.items():
        back = d - pd.DateOffset(months=3)
        if back in nir.index:
            w.put("nir_chg_3m", d.date(), val - nir[back], "USD mn", "nir_chg_3m",
                  f"nir {d:%b %Y}={val:,.1f} − nir {back:%b %Y}={nir[back]:,.1f} (CBE)")
        oil = v.value_at("imports_oil_fy", d.date() - timedelta(days=365))
        non = v.value_at("imports_nonoil_fy", d.date() - timedelta(days=365))
        if oil and non and oil.date == non.date:
            imp = oil.value + non.value
            w.put("nir_months_imports", d.date(), (val / 1000.0) / (imp / 12.0), "months", "nir_months_imports",
                  f"nir {d:%b %Y}={val:,.1f} mn / ({_cite(oil)} + {_cite(non)}) /12")
        nxt = v.frame("ext_debt_service_sched", include_future=True)
        nxt = nxt[nxt["obs_date"] == date(d.year + 1, 1, 1)]
        if not nxt.empty:
            ds = float(nxt["value"].iloc[-1])
            w.put("debt_service_next_year_to_nir", d.date(), ds / (val / 1000.0) * 100.0, "%",
                  "debt_service_next_year_to_nir",
                  f"ext_debt_service_sched {d.year + 1}={ds:g} bn ({nxt['source_name'].iloc[-1]}) / nir {d:%b %Y}={val:,.1f} mn")
    rem = v.series("remittances")
    for d in rem.index:
        months = [d - pd.DateOffset(months=k) for k in range(12)]
        if all(m in rem.index for m in months):
            w.put("remittances_12m_sum", d.date(), float(sum(rem[m] for m in months)), "USD bn", "remittances_12m_sum",
                  f"sum of 12 monthly remittance prints {months[-1]:%b %Y}–{d:%b %Y} (CBE press releases)")
    for key in ("suez", "babelmandeb", "hormuz"):
        s = v.series(f"{key}_transits")
        if s.empty:
            continue
        base = s[(s.index >= "2023-01-01") & (s.index <= "2023-12-31")]
        if len(base) < 300:
            continue
        b = base.mean()
        ma = s.rolling(7, min_periods=7).mean().dropna()
        for d, m in ma[ma.index >= "2024-01-01"].items():
            w.put(f"{key}_ratio_7dma", d.date(), m / b, "ratio", "transits_ratio",
                  f"{key}_transits 7-day mean {m:.1f} to {d.date()} / 2023 daily mean {b:.1f} (IMF PortWatch, {len(base)} days)")


def build_hot_money(v: DataView, w: Writer) -> None:
    """CIB Cairo vs London (same-day closes only) and EGX30 in dollars."""
    loc, gdr = v.series("cib_local"), v.series("cib_gdr")
    for d, lp in loc.items():
        if d not in gdr.index:
            continue
        implied = lp / gdr[d]
        dd = d.date()
        ins = f"cib_local={lp:g} EGP (Yahoo COMI.CA) / cib_gdr={gdr[d]:g} USD (Yahoo CBKD.IL), {dd}, 1 GDR = 1 share"
        w.put("cib_gdr_implied_fx", dd, implied, "EGP per USD", "cib_gdr_implied_fx", ins)
        off = v.value_at("fx_cbe_official", dd)
        if off is not None and (dd - off.date).days <= 3:
            w.put("cib_gdr_premium_pct", dd, gap_pct(implied, off.value), "%", "gap_pct", f"{ins}; {_cite(off)}")
    for d, e in v.series("egx30").items():
        off = v.value_at("fx_cbe_official", d.date())
        if off is not None and (d.date() - off.date).days <= 3:
            w.put("egx30_usd", d.date(), e / off.value, "index", "egx30_usd", f"egx30={e:g} (Yahoo ^CASE30) / {_cite(off)}")


def build_real_and_global(v: DataView, w: Writer) -> None:
    p = v.series("pmi")
    for i, (d, val) in enumerate(p.items()):
        w.put("pmi_implied_gdp", d.date(), pmi_implied_gdp(val), "%", "pmi_implied_gdp",
              f"pmi={val:g} ({d:%b %Y}, S&P Global) × 0.269 − 8.62 (S&P Global formula per spec)")
        win = p[(p.index <= d) & (p.index > d - pd.DateOffset(months=3))]
        if len(win) == 3:
            w.put("pmi_3m_avg", d.date(), win.mean(), "index", "pmi_3m_avg",
                  "pmi " + ", ".join(f"{x:%b}={y:g}" for x, y in win.items()))
    for src, out in (("us_cpi", "us_cpi_yoy"), ("us_core_cpi", "us_core_cpi_yoy")):
        s = v.series(src)
        for d, val in s.items():
            back = d - pd.DateOffset(years=1)
            if back in s.index:
                w.put(out, d.date(), pct_change(val, s[back]), "%", "pct_change",
                      f"{src} {d:%b %Y}={val:g} vs {back:%b %Y}={s[back]:g} (BLS via FRED)")


def build_eda(v: DataView, w: Writer) -> None:
    """6-month window ending each CPI month: needs FX, six m/m CPI prints and the ODR at both ends."""
    mom = v.series("cpi_urban_mom")
    fx = v.series("fx_cbe_official")
    if mom.empty or fx.empty:
        return
    for d in mom.index:
        months = [d - pd.DateOffset(months=k) for k in range(5, -1, -1)]
        if not all(m in mom.index for m in months):
            continue
        end = period_end(d.date(), "monthly")
        start = period_end((d - pd.DateOffset(months=6)).date(), "monthly")
        f1, f0 = v.value_at("fx_cbe_official", end), v.value_at("fx_cbe_official", start)
        o1, o0 = v.value_at("cbe_odr", end), v.value_at("cbe_odr", start)
        if not (f1 and f0 and o1 and o0) or (end - f1.date).days > 7 or (start - f0.date).days > 7:
            continue
        fx_chg = pct_change(f1.value, f0.value)
        cpi_chg = cumulative_from_mom([mom[m] for m in months])
        odr_chg = pct_change(o1.value, o0.value)
        w.put("eda_signal", d.date(), eda_signal(fx_chg, cpi_chg, odr_chg), "%", "eda_signal",
              f"0.6×USD/EGP {fx_chg:+.2f}% ({f0.date}→{f1.date}) + 0.3×urban CPI index {cpi_chg:+.2f}% "
              f"(6 m/m prints to {d:%b %Y}) + 0.1×ODR {odr_chg:+.2f}% — reconstruction of Decision 480 (verify vs Gazette)")


def compute_all(conn) -> dict:
    w = Writer(conn)
    steps = [build_real_rates, build_gold, build_fx, build_energy, build_brent_spread, build_brent_quarter, build_external,
             build_real_and_global, build_hot_money]
    for fn in steps:
        try:
            fn(DataView(conn), w)  # fresh view so later steps see earlier outputs
            conn.commit()
        except Exception as e:  # noqa: BLE001
            log.warning("derive step %s failed: %s", fn.__name__, e)
            conn.rollback()
    try:
        build_eda(DataView(conn), w)
        conn.commit()
    except Exception as e:  # noqa: BLE001
        log.warning("derive eda failed: %s", e)
    log.info("derived rows written: %s %s", w.n, w.counts)
    return {"rows": w.n, "by_series": w.counts}
