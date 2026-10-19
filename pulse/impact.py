"""Impact outlook: "if the dollar move persists, how much will prices rise — how sure are we — and what usually follows?"

Built from Egypt's own history (no invented numbers):
  * Price outlook per category = today's inflation pace (last 12 months, scaled to the horizon) + the median
    EXTRA inflation seen after past dollar moves of similar size (3-month rise of 2–8% = 'moderate',
    ≥ 8% = 'large'). Episodes are counted once (months within ~3 months of each other are one episode).
  * Accuracy = leave-one-out test: each past episode is predicted from all the others; we report the average
    error (percentage points), how often the real outcome fell inside the range, and the error of the plain
    'last year's pace continues' rule for comparison.
  * Odds: how often the dollar kept rising the month after a ≥ 2% monthly rise (since 2005); how often a
    moderate move escalated into a large one within 3 months; how often the CBE raised rates within 3 months.
Data: IMF CPI by category (2010–) and USD/EGP monthly average (2005–), CBE official rate (daily) for recent
months, CBE MPC decisions parsed from press releases. Statistics from history — not a promise.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import DataView

CATS = [  # id, series, EN, AR
    ("all", "cpi_imf_all", "All prices", "كل الأسعار"),
    ("food", "cpi_imf_food", "Food & drinks", "الأكل والمشروبات"),
    ("transport", "cpi_imf_transport", "Transport & fuel", "المواصلات والوقود"),
    ("health", "cpi_imf_health", "Medicine & health", "الأدوية والصحة"),
    ("housing", "cpi_imf_housing", "Housing & utilities", "السكن والمرافق"),
]
H = 6  # months ahead
MODERATE, LARGE = 2.0, 8.0


def _monthly(v: DataView, sid: str) -> pd.Series:
    s = v.series(sid)
    return s.resample("MS").last().dropna() if len(s) else s


def fx_monthly(v: DataView) -> pd.Series:
    imf = _monthly(v, "fx_imf_avg")
    cbe = v.series("fx_cbe_official")
    cbe_m = cbe.resample("MS").mean().dropna() if len(cbe) else cbe
    if len(imf) == 0:
        return cbe_m
    return pd.concat([imf, cbe_m[cbe_m.index > imf.index[-1]]]).sort_index()


def _episodes(P: pd.Series, FX: pd.Series, lo: float, hi: float) -> pd.DataFrame:
    df = pd.DataFrame({"p": np.log(P), "fx": np.log(FX)}).dropna().asfreq("MS")
    d = pd.DataFrame(index=df.index)
    d["f3"] = 100 * (np.exp(df.fx - df.fx.shift(3)) - 1)
    d["y"] = 100 * (np.exp(df.p.shift(-H) - df.p) - 1)
    d["pace"] = 100 * (np.exp((df.p - df.p.shift(12)) * H / 12) - 1)
    d = d.dropna()
    m = d[(d.f3 >= lo) & (d.f3 < hi)]
    keep, last = [], None
    for t in m.index:
        if last is None or (t - last).days > 100:
            keep.append(t)
        last = t
    e = d.loc[keep].copy()
    e["extra"] = e.y - e.pace
    return e


def _group_stats(e: pd.DataFrame) -> dict | None:
    if len(e) < 5:
        return None
    errs, cover, naive = [], [], []
    for i in e.index:
        o = e.extra.drop(i)
        pred = e.at[i, "pace"] + o.median()
        errs.append(abs(e.at[i, "y"] - pred))
        naive.append(abs(e.at[i, "y"] - e.at[i, "pace"]))
        cover.append(e.at[i, "pace"] + o.quantile(.1) <= e.at[i, "y"] <= e.at[i, "pace"] + o.quantile(.9))
    return {"n": len(e), "extra_med": float(e.extra.median()), "extra_p10": float(e.extra.quantile(.1)), "extra_p90": float(e.extra.quantile(.9)),
            "mae": float(np.mean(errs)), "naive_mae": float(np.mean(naive)), "hits": int(np.sum(cover)),
            "episodes": [t.strftime("%Y-%m") for t in e.index]}


def _pace_now(P: pd.Series) -> float | None:
    if len(P) < 13:
        return None
    return float(100 * (np.exp(np.log(P.iloc[-1] / P.iloc[-13]) * H / 12) - 1))


def odds(v: DataView, FX: pd.Series) -> dict:
    out: dict = {}
    ch = 100 * FX.pct_change()
    ep = pd.DataFrame({"now": ch, "next": ch.shift(-1)}).dropna()
    ep = ep[ep.now >= 2]
    if len(ep) >= 5:
        out["keeps_rising"] = {"n": len(ep), "up": int((ep.next > 0.5).sum()), "flat": int(ep.next.between(-0.5, 0.5).sum()),
                               "down": int((ep.next < -0.5).sum()), "since": FX.index[0].strftime("%Y")}
    f3 = 100 * (FX / FX.shift(3) - 1)
    fut = pd.concat([f3.shift(-k) for k in (1, 2, 3)], axis=1).max(axis=1)
    mod = pd.DataFrame({"f3": f3, "fut": fut}).dropna()
    mod = mod[(mod.f3 >= MODERATE) & (mod.f3 < LARGE)]
    keep, last = [], None
    for t in mod.index:
        if last is None or (t - last).days > 100:
            keep.append(t)
        last = t
    mod = mod.loc[keep]
    if len(mod) >= 5:
        out["escalates"] = {"n": len(mod), "k": int((mod.fut >= LARGE).sum()), "since": FX.index[0].strftime("%Y")}
    dec = v.series("cbe_mpc_decision")
    if len(dec) >= 20:
        trig = f3[(f3 >= MODERATE)].dropna()
        trig = trig[trig.index >= dec.index[0]]
        keep, last = [], None
        for t in trig.index:
            if last is None or (t - last).days > 100:
                keep.append(t)
            last = t
        hikes = sum(bool(((dec.index > t) & (dec.index <= t + pd.DateOffset(months=3)) & (dec > 0)).any()) for t in keep)
        out["cbe_hikes"] = {"n": len(keep), "k": int(hikes), "since": dec.index[0].strftime("%Y")}
    return out


def build_impact(v: DataView, move_pct: float, pace_month: float) -> dict | None:
    FX = fx_monthly(v)
    if len(FX) < 60:
        return None
    off = v.series("fx_cbe_official")
    f3_now = None
    if len(off) > 70:
        f3_now = float(100 * (off.iloc[-1] / off[off.index <= off.index[-1] - pd.Timedelta(days=91)].iloc[-1] - 1))
    f3_now = f3_now if f3_now is not None else move_pct

    def group(f3):
        return "large" if f3 >= LARGE else "moderate" if f3 >= MODERATE else "small"

    g_now, g_more = group(f3_now), group(f3_now + pace_month)
    cats = []
    for cid, sid, en, ar in CATS:
        P = _monthly(v, sid)
        if cid == "all":  # months the IMF has not posted yet come from CBE's monthly change
            mom = _monthly(v, "cpi_urban_mom")
            if len(P) and len(mom):
                for dt, val in mom[mom.index > P.index[-1]].items():
                    P.loc[dt] = P.iloc[-1] * (1 + val / 100)
                P = P.sort_index()
        pace = _pace_now(P)
        if pace is None:
            continue
        st = {g: _group_stats(_episodes(P, FX, lo, hi)) for g, lo, hi in (("moderate", MODERATE, LARGE), ("large", LARGE, 1e9))}
        st["small"] = None

        stale = (pd.Timestamp.today() - P.index[-1]).days > 150   # category series the IMF has not updated

        def outlook(g):
            s = st.get(g)
            if not s:
                return {"mid": None if stale else round(pace, 1), "lo": None, "hi": None, "extra": 0.0, "xlo": None, "xhi": None}
            return {"mid": None if stale else round(pace + s["extra_med"], 1), "lo": None if stale else round(pace + s["extra_p10"], 1),
                    "hi": None if stale else round(pace + s["extra_p90"], 1), "extra": round(s["extra_med"], 1),
                    "xlo": round(s["extra_p10"], 1), "xhi": round(s["extra_p90"], 1)}

        cats.append({"id": cid, "title": [en, ar], "pace": None if stale else round(pace, 1), "stale": stale, "data_to": P.index[-1].strftime("%Y-%m"),
                     "now": outlook(g_now), "more": outlook(g_more),
                     "test": {g: ({k: (round(x, 2) if isinstance(x, float) else x) for k, x in s.items()} if s else None) for g, s in st.items() if g != "small"}})
    if not cats:
        return None
    allc = next(c for c in cats if c["id"] == "all")
    t = allc["test"].get(g_now if g_now != "small" else "moderate") or {}
    n, hits = t.get("n", 0), t.get("hits", 0)
    conf = "low" if n < 10 or (n and hits / n < 0.7) else "medium"
    return {"f3_now": round(f3_now, 1), "group_now": g_now, "group_more": g_more, "pace_month": round(pace_month, 1), "h": H,
            "cats": cats, "odds": odds(v, FX), "confidence": conf,
            "sources": [{"name": "IMF CPI by category (SDMX API)", "url": "https://data.imf.org/en/datasets/IMF.STA:CPI"},
                        {"name": "IMF exchange rates + CBE official rate", "url": "https://data.imf.org/en/datasets/IMF.STA:ER"},
                        {"name": "CBE MPC press releases", "url": "https://www.cbe.org.eg/en/monetary-policy"}],
            "method": ["Outlook = today's inflation pace + the extra inflation seen after past dollar moves of the same size (Egypt, 2010–2026). "
                       "Accuracy = each past episode predicted from the others. History, not a promise.",
                       "التوقع = سرعة التضخم الحالية + الزيادة الإضافية اللي حصلت بعد حركات دولار بنفس الحجم في مصر (2010–2026). "
                       "الدقة = كل مرة في الماضي اتوقعناها من باقي المرات. ده تاريخ مش وعد."]}
