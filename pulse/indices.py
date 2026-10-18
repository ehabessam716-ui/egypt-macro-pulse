"""Composite indices (SPEC §7): Pound Pressure Index (PPI) + Inflation Pressure + Growth, and a backtest.

Never fills gaps: missing or very stale inputs simply lower coverage_pct. PPI below the
minimum coverage is stored but flagged 'insufficient data' (greyed out in outputs).
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .core import get_logger, load_yaml, today_cairo
from .data import DataView, load_base
from .db import to_json
from .events import subindex_event_points
from .rules import evaluate

log = get_logger("pulse.indices")


def score_input(s: pd.Series, as_of: date, window_years: int = 3, min_obs: int = 24, clip: float = 3.0) -> tuple[float, float] | None:
    """Return (z, score) for the latest value vs the trailing window, or None if not enough history."""
    s = s.dropna()
    if s.empty:
        return None
    win = s[s.index > pd.Timestamp(as_of) - pd.DateOffset(years=window_years)]
    if len(win) < min_obs:
        return None
    sd = win.std(ddof=1)
    if not sd or math.isnan(sd):
        return None
    z = float(np.clip((win.iloc[-1] - win.mean()) / sd, -clip, clip))
    return z, 100.0 * math.tanh(z / 2.0)


def _component_inputs(v: DataView, inputs: list[dict], as_of: date, m: dict) -> tuple[list[dict], int]:
    comps, available = [], 0
    for inp in inputs:
        sid = inp["series"]
        o = v.latest(sid)
        entry = {"series": sid, "sign": inp["sign"], "kind": "input"}
        if o is None or o.stale >= 2:
            entry["status"] = "missing" if o is None else "too stale"
            comps.append(entry)
            continue
        sc = score_input(v.series(sid), as_of, m["window_years"], m["min_obs"], m["clip"])
        if sc is None:
            entry.update(status="history < min_obs", value=o.value, obs_date=o.date.isoformat())
            comps.append(entry)
            continue
        available += 1
        z, score = sc
        entry.update(status="ok", value=o.value, obs_date=o.date.isoformat(), source=o.source_name, z=round(z, 3),
                     score=round(score * inp["sign"], 2))
        comps.append(entry)
    return comps, available


def compute(conn, as_of: date | None = None, point_in_time: bool = False, base=None, rule_results=None) -> dict:
    as_of = as_of or today_cairo()
    cfg = load_yaml("indices.yaml")
    m = cfg["method"]
    v = DataView(conn, as_of, point_in_time=point_in_time, base=base)
    rules = rule_results if rule_results is not None else evaluate(conn, as_of, point_in_time, base)
    rcfg = load_yaml("rules.yaml")["rules"]
    ev_pts = subindex_event_points(conn, as_of)
    out: dict = {"as_of": as_of.isoformat(), "subindices": {}, "extra": {}}
    tot_w = cov_w = val_w = 0.0
    weighted = 0.0
    for sid, sc in cfg["ppi"]["subindices"].items():
        comps, avail = _component_inputs(v, sc["inputs"], as_of, m)
        rule_comps = []
        for rid, r in rules.items():
            if r.fired and r.direction != 0 and sid in rcfg.get(rid, {}).get("affects", []):
                rule_comps.append({"rule": rid, "kind": "rule", "score": round(100 * r.strength * r.direction, 2)})
        scores = [c["score"] for c in comps if c.get("status") == "ok"] + [c["score"] for c in rule_comps]
        evp = ev_pts.get(sid, 0.0)
        coverage = avail / len(sc["inputs"]) * 100 if sc["inputs"] else 0.0
        value = None
        if scores or evp:
            base_val = float(np.mean(scores)) if scores else 0.0
            value = float(np.clip(base_val + evp, -100, 100))
        out["subindices"][sid] = {"name_en": sc["name_en"], "name_ar": sc["name_ar"], "weight": sc["weight"],
                                  "value": None if value is None else round(value, 1), "coverage_pct": round(coverage, 1),
                                  "event_points": round(evp, 2), "components": comps + rule_comps}
        tot_w += sc["weight"]
        cov_w += sc["weight"] * coverage / 100
        if value is not None:
            weighted += sc["weight"] * value
            val_w += sc["weight"]
    ppi = weighted / val_w if val_w else None
    coverage = cov_w / tot_w * 100 if tot_w else 0.0
    out["ppi"] = {"value": None if ppi is None else round(ppi, 1), "coverage_pct": round(coverage, 1),
                  "sufficient": coverage >= cfg["ppi"]["min_coverage_pct"],
                  "min_coverage_pct": cfg["ppi"]["min_coverage_pct"]}
    for xid, xc in cfg.get("extra", {}).items():
        comps, avail = _component_inputs(v, xc["inputs"], as_of, m)
        rule_comps = [{"rule": rid, "kind": "rule", "score": round(100 * rules[rid].strength * sign, 2)}
                      for rid, sign in (xc.get("rules") or {}).items() if rid in rules and rules[rid].fired]
        scores = [c["score"] for c in comps if c.get("status") == "ok"] + [c["score"] for c in rule_comps]
        out["extra"][xid] = {"name_en": xc["name_en"], "name_ar": xc["name_ar"],
                             "value": round(float(np.clip(np.mean(scores), -100, 100)), 1) if scores else None,
                             "coverage_pct": round(avail / len(xc["inputs"]) * 100, 1), "components": comps + rule_comps}
    return out


def store(conn, res: dict, kind: str = "live") -> None:
    d = res["as_of"]
    conn.execute("DELETE FROM index_values WHERE run_date=? AND kind=?", (d, kind))
    rows = [("PPI", res["ppi"]["value"], {"sufficient": res["ppi"]["sufficient"]}, res["ppi"]["coverage_pct"])]
    rows += [(f"PPI_{k}", s["value"], {"components": s["components"], "event_points": s["event_points"],
                                       "weight": s["weight"]}, s["coverage_pct"]) for k, s in res["subindices"].items()]
    rows += [(k.upper(), s["value"], {"components": s["components"]}, s["coverage_pct"]) for k, s in res["extra"].items()]
    for iid, val, comp, cov in rows:
        conn.execute("INSERT INTO index_values VALUES (?,?,?,?,?,?)", (d, iid, val, to_json(comp), cov, kind))


def compute_indices(conn, as_of: date | None = None) -> dict:
    res = compute(conn, as_of)
    store(conn, res)
    conn.commit()
    log.info("PPI=%s coverage=%.0f%% (%s) | %s", res["ppi"]["value"], res["ppi"]["coverage_pct"],
             "ok" if res["ppi"]["sufficient"] else "insufficient data",
             ", ".join(f"{k}={s['value']}" for k, s in res["subindices"].items()))
    return {"ppi": res["ppi"], "subindices": {k: s["value"] for k, s in res["subindices"].items()},
            "extra": {k: s["value"] for k, s in res["extra"].items()}}


def run_backtest(conn, weeks: int = 104) -> dict:
    """Weekly point-in-time PPI for the last `weeks` weeks (learning only, no predictive claims)."""
    base = load_base(conn)
    end = today_cairo()
    n = 0
    for k in range(weeks, 0, -1):
        d = end - timedelta(weeks=k)
        res = compute(conn, d, point_in_time=True, base=base)
        store(conn, res, kind="backtest")
        n += 1
    conn.commit()
    log.info("backtest: %d weekly points", n)
    return {"points": n}
