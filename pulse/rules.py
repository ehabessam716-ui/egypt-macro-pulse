"""Rule engine (SPEC §6). Each rule returns a RuleResult; texts/thresholds come from config/rules.yaml.

A rule whose inputs are missing or too stale is recorded as 'not evaluable' (it never guesses).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

import numpy as np
import pandas as pd

from .core import get_logger, load_yaml, today_cairo
from .data import DataView, Obs
from .db import to_json
from .events import active_events

log = get_logger("pulse.rules")
LATIN = re.compile(r"[A-Za-z]")


@dataclass
class RuleResult:
    rule_id: str
    evaluable: bool
    fired: bool = False
    strength: float = 0.0
    direction: float = 0.0
    inputs: list[dict] = field(default_factory=list)
    vals: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    explanation_en: str = ""
    explanation_ar: str = ""

    @property
    def signed(self) -> float:
        return self.strength * self.direction if self.fired else 0.0


class Ctx:
    def __init__(self, conn, as_of: date | None = None, point_in_time: bool = False, base=None):
        self.conn = conn
        self.as_of = as_of or today_cairo()
        self.v = DataView(conn, self.as_of, point_in_time=point_in_time, base=base)
        self.cfg = load_yaml("rules.yaml")["rules"]
        self.events = active_events(conn, self.as_of, include_tags=True)
        self.results: dict[str, RuleResult] = {}

    def p(self, rid: str) -> dict:
        return self.cfg[rid].get("params", {})

    def get(self, sid: str, r: RuleResult, max_level: int = 1, fallback: bool = False) -> Obs | None:
        o = self.v.resolved(sid, max_level) if fallback else self.v.fresh(sid, max_level)
        if o is None:
            r.missing.append(sid)
        else:
            r.inputs.append(o.cite())
        return o

    def events_of(self, *types: str, within_days: int | None = None) -> list[dict]:
        out = [e for e in self.events if e["event_type"] in types]
        if within_days is not None:
            out = [e for e in out if (self.as_of - date.fromisoformat(e["event_date"])).days <= within_days]
        return out


RULES: dict[str, Callable[[Ctx, RuleResult], None]] = {}


def rule(rid: str):
    def wrap(fn):
        RULES[rid] = fn
        return fn
    return wrap


def fire(r: RuleResult, direction: float, strength: float, **vals) -> None:
    r.fired = True
    r.direction = direction
    r.strength = float(max(0.0, min(1.0, strength)))
    r.vals.update(vals)


def no_eval(r: RuleResult) -> None:
    r.evaluable = False


def _chg(s: pd.Series, n: int) -> float | None:
    s = s.dropna()
    if len(s) <= n:
        return None
    return (s.iloc[-1] / s.iloc[-1 - n] - 1) * 100


# ======================================================================= FX & markets
@rule("FX01")
def fx01(c: Ctx, r: RuleResult):
    p = c.p("FX01")
    nir = c.v.series("nir")
    fx20 = c.get("fx_chg_20d", r)
    gold = c.v.fresh("gold_gap_pct")
    par = c.v.fresh("fx_parallel")
    if len(nir) < p["nir_falling_months"] + 1 or fx20 is None or (gold is None and par is None):
        r.missing += [] if len(nir) > p["nir_falling_months"] else ["nir (4 months)"]
        return no_eval(r)
    diffs = np.diff(nir.values[-(p["nir_falling_months"] + 1):])
    gaps = []
    if gold:
        r.inputs.append(gold.cite())
        gaps.append(gold.value)
    off = c.v.fresh("fx_cbe_official")
    if par and off:
        r.inputs.append(par.cite())
        gaps.append((par.value / off.value - 1) * 100)
    gap = max(gaps)
    r.vals.update(nir_months=p["nir_falling_months"], fx_chg_20d=fx20.value, gap=gap)
    if all(diffs < 0) and abs(fx20.value) < p["fx_flat_pct"] and gap > p["gap_pct"]:
        fire(r, 1, 1.0)


@rule("FX02")
def fx02(c: Ctx, r: RuleResult):
    p = c.p("FX02")
    cands = []
    g = c.v.fresh("gold_gap_pct")
    if g:
        r.inputs.append(g.cite())
        cands.append(("gold-implied rate", "سعر الدولار المحسوب من الدهب", g.value))
    par, off = c.v.fresh("fx_parallel"), c.v.fresh("fx_cbe_official")
    if par and off:
        r.inputs += [par.cite(), off.cite()]
        cands.append(("parallel-market rate", "سعر السوق الموازية", (par.value / off.value - 1) * 100))
    if not cands:
        r.missing += ["gold_gap_pct", "fx_parallel"]
        return no_eval(r)
    name, name_ar, gap = max(cands, key=lambda x: x[2])
    level, level_ar, st = "noise", "تذبذب عادي", 0.0
    if gap > p["severe"]:
        level, level_ar, st = "severe", "خطير", 1.0
    elif gap > p["alert"]:
        level, level_ar, st = "alert", "إنذار", 0.66
    elif gap > p["watch"]:
        level, level_ar, st = "watch", "مراقبة", 0.33
    elif abs(gap) > p["noise"]:
        level, level_ar = "outside the noise band but below watch", "برة حدود التذبذب لكن أقل من مستوى المراقبة"
    r.vals.update(gap_name=name, gap_name_ar=name_ar, gap=gap, level=level, level_ar=level_ar, noise=p["noise"])
    if st > 0:
        fire(r, 1, st)


@rule("FX03")
def fx03(c: Ctx, r: RuleResult):
    p = c.p("FX03")
    egx = c.v.series("egx_foreign_net")
    hold = c.v.series("foreign_tbills_holdings")
    if len(egx) < p["sessions"] and len(hold) < 2:
        r.missing += ["egx_foreign_net (MANUAL)", "foreign_tbills_holdings (MANUAL)"]
        return no_eval(r)
    details, details_ar = [], []
    if len(egx) >= p["sessions"] and (egx.iloc[-p["sessions"]:] < 0).all():
        details.append(f"EGX foreigners net sellers {p['sessions']} sessions in a row")
        details_ar.append(f"الأجانب بايعين في البورصة {p['sessions']} جلسات ورا بعض")
    if len(hold) >= 2 and (hold.iloc[-1] / hold.iloc[-2] - 1) * 100 < -p["tbill_drop_pct"]:
        details.append(f"non-resident T-bill holdings fell {(hold.iloc[-1] / hold.iloc[-2] - 1) * 100:.1f}% m/m")
        details_ar.append("حيازة الأجانب لأذون الخزانة نزلت بقوة")
    r.vals.update(detail="; ".join(details), detail_ar="، و".join(details_ar))
    if details:
        fire(r, 1, 0.5 * len(details))


@rule("FX04")
def fx04(c: Ctx, r: RuleResult):
    p = c.p("FX04")
    details, details_ar = [], []
    seen = False
    for key, label, label_ar in (("3m", "91-day", "3 شهور"), ("6m", "182-day", "6 شهور"), ("9m", "273-day", "9 شهور"),
                                 ("12m", "1-year", "سنة")):
        btc, acc = c.v.fresh(f"tbill_{key}_btc"), c.v.fresh(f"tbill_{key}_accepted_ratio")
        if btc is None or acc is None:
            continue
        seen = True
        r.inputs += [btc.cite(), acc.cite()]
        if btc.value < p["btc_min"]:
            details.append(f"{label} bid-to-cover {btc.value:.2f} on {btc.date}")
            details_ar.append(f"نسبة التغطية لأذون {label_ar} ضعيفة")
        if acc.value < p["accepted_min"]:
            details.append(f"{label} accepted only {acc.value:.0%} of the amount offered on {acc.date}")
            details_ar.append(f"الحكومة قبلت {acc.value * 100:.0f}% بس من المطلوب في أذون {label_ar}")
        y = c.v.series(f"tbill_{key}_yield")
        if len(y) >= 2:
            back = y[y.index <= y.index[-1] - pd.Timedelta(weeks=p["weeks"])]
            if not back.empty and (y.iloc[-1] - back.iloc[-1]) * 100 > p["yield_jump_bp"]:
                details.append(f"{label} yield up {(y.iloc[-1] - back.iloc[-1]) * 100:.0f} bp in {p['weeks']} weeks")
                details_ar.append(f"عائد أذون {label_ar} طلع جامد في {p['weeks']} أسابيع")
    if not seen:
        r.missing.append("tbill auctions")
        return no_eval(r)
    r.vals.update(detail="; ".join(details), detail_ar="، و".join(details_ar))
    if details:
        fire(r, 1, min(1.0, 0.34 * len(details)))


@rule("FX05")
def fx05(c: Ctx, r: RuleResult):
    p = c.p("FX05")
    o = c.get("fx_chg_5d", r)
    if o is None:
        return no_eval(r)
    r.vals.update(fx_chg_5d=o.value, pct_5d=p["pct_5d"])
    if o.value > p["pct_5d"]:
        fire(r, 1, min(1.0, o.value / 5))


# ======================================================================= monetary & inflation
@rule("MO01")
def mo01(c: Ctx, r: RuleResult):
    p = c.p("MO01")
    real, cpi = c.get("real_headline", r), c.get("cpi_urban_yoy", r)
    odr = c.v.latest("cbe_odr")
    if real is None or cpi is None or odr is None:
        return no_eval(r)
    r.inputs.append(odr.cite())
    r.vals.update(real=real.value, odr=odr.value, cpi=cpi.value, verdict="Inside the 2–5 pp band (tool default): neutral.",
                  verdict_ar="ده في النطاق العادي.")
    if real.value < p["low"]:
        r.vals.update(verdict="Below +2 pp: the carry cushion for foreign investors is thin (pressure).",
                      verdict_ar="الفايدة الحقيقية قليلة، فالمستثمر الأجنبي ممكن يمشي.")
        fire(r, 1, min(1.0, (p["low"] - real.value) / 4 + 0.25))
    elif real.value > p["high"]:
        r.vals.update(verdict="Above +5 pp: a fat cushion that attracts carry inflows (relief).",
                      verdict_ar="الفايدة الحقيقية عالية، وده بيجذب الأموال الأجنبية وبيدعم الجنيه.")
        fire(r, -1, min(1.0, (real.value - p["high"]) / 5 + 0.25))


@rule("MO02")
def mo02(c: Ctx, r: RuleResult):
    p = c.p("MO02")
    rc, re_ = c.get("real_core", r), c.get("real_expected", r)
    if rc is None or re_ is None:
        return no_eval(r)
    div = abs(rc.value - re_.value)
    r.vals.update(real_core=rc.value, real_exp=re_.value, div=div)
    if div > p["gap_pp"]:
        fire(r, 1, min(1.0, div / 6))


@rule("MO03")
def mo03(c: Ctx, r: RuleResult):
    r.missing.append("consensus (PAID/MANUAL)")
    return no_eval(r)


@rule("MO04")
def mo04(c: Ctx, r: RuleResult):
    p = c.p("MO04")
    s = c.v.series("cpi_urban_mom")
    last = c.get("cpi_urban_mom", r)
    if last is None or len(s) < p["months"]:
        return no_eval(r)
    tail = s.iloc[-p["months"]:]
    r.vals.update(mom=p["mom"], months=p["months"], detail=", ".join(f"{d:%b}={v:.1f}%" for d, v in tail.items()))
    if (tail > p["mom"]).all():
        fire(r, 0, 0.6)


@rule("MO05")
def mo05(c: Ctx, r: RuleResult):
    p = c.p("MO05")
    o = c.get("fx_chg_3m", r)
    if o is None:
        return no_eval(r)
    r.vals.update(fx_chg_3m=o.value)
    if o.value > p["fx_3m_pct"]:
        fire(r, 1, min(1.0, o.value / 15))


@rule("MO06")
def mo06(c: Ctx, r: RuleResult):
    p = c.p("MO06")
    fx = c.get("fx_chg_3m", r)
    cpi, real = c.v.series("cpi_urban_yoy"), c.v.series("real_headline")
    if fx is None or len(cpi) < 2 or len(real) < 2 or c.v.fresh("cpi_urban_yoy") is None:
        r.missing += ["cpi_urban_yoy (2 months)", "real_headline (2 months)"]
        return no_eval(r)
    r.vals.update(fx_chg_3m=fx.value, cpi=cpi.iloc[-1], cpi_prev=cpi.iloc[-2], real=real.iloc[-1], real_prev=real.iloc[-2])
    if fx.value > p["fx_3m_pct"] and cpi.iloc[-1] > cpi.iloc[-2] and real.iloc[-1] < real.iloc[-2]:
        fire(r, 1, 1.0)


@rule("MO07")
def mo07(c: Ctx, r: RuleResult):
    p = c.p("MO07")
    core = c.v.series("cpi_core_mom")
    if len(core) < 2:
        r.missing.append("cpi_core_mom (2 months)")
        return no_eval(r)
    hikes = c.events_of("fuel_price_hike", within_days=p["days"])
    r.vals.update(days=p["days"], core=core.iloc[-1], core_prev=core.iloc[-2])
    if hikes and core.iloc[-1] > core.iloc[-2]:
        r.inputs += [{"event": e["title_en"], "date": e["event_date"], "url": e["source_url"]} for e in hikes]
        fire(r, 1, 0.6)


@rule("MO08")
def mo08(c: Ctx, r: RuleResult):
    p = c.p("MO08")
    g, pr = c.get("credit_gov", r), c.get("credit_private", r)
    if g is None or pr is None:
        return no_eval(r)
    r.vals.update(gap=g.value - pr.value)
    if g.value - pr.value > p["gap_pp"]:
        fire(r, 0, 0.5)


# ======================================================================= external
@rule("EX01")
def ex01(c: Ctx, r: RuleResult):
    p = c.p("EX01")
    s = c.v.series("remittances_yoy")
    last = c.get("remittances_yoy", r)
    if last is None:
        return no_eval(r)
    tail = s[s.index > s.index[-1] - pd.DateOffset(months=3)]
    yoy = float(tail.mean())
    r.vals.update(yoy=yoy, n=len(tail), verdict="Between 0% and 20%: neutral (tool default).",
                  verdict_ar="ده نمو عادي.")
    if yoy < p["low"]:
        r.vals.update(verdict="Falling remittances = fewer dollars from Egyptians abroad (pressure).",
                      verdict_ar="التحويلات بتقل، يعني دولارات أقل جاية من برة.")
        fire(r, 1, min(1.0, abs(yoy) / 20 + 0.3))
    elif yoy > p["high"]:
        r.vals.update(verdict="Above 20%: a strong dollar inflow (relief).",
                      verdict_ar="ده نمو قوي، ودولارات كتير داخلة بتدعم الجنيه.")
        fire(r, -1, min(1.0, (yoy - p["high"]) / 20 + 0.4))


@rule("EX02")
def ex02(c: Ctx, r: RuleResult):
    p = c.p("EX02")
    o = c.get("suez_ratio_7dma", r)
    if o is None:
        return no_eval(r)
    r.vals.update(ratio=o.value, ratio_pct=o.value * 100, verdict="Between weak and recovered: neutral.",
                  verdict_ar="الحركة في المنطقة الوسط.")
    if o.value < p["weak"]:
        r.vals.update(verdict="Below 60% of normal: Suez revenue (a key dollar source) is depressed.",
                      verdict_ar="الحركة أقل من 60% من الطبيعي، وإيرادات القناة بالدولار ضعيفة.")
        fire(r, 1, min(1.0, (p["weak"] - o.value) / 0.4 + 0.4))
    elif o.value > p["recovered"]:
        r.vals.update(verdict="Above 85% of normal: traffic has recovered (relief).",
                      verdict_ar="الحركة رجعت قريب من الطبيعي، وده كويس للدولار.")
        fire(r, -1, 0.5)


def _war(c: Ctx) -> list[dict]:
    return [e for e in c.events_of("regional_war_escalation") if e["confidence"] in ("confirmed", "reported")]


@rule("EX03")
def ex03(c: Ctx, r: RuleResult):
    t = c.v.series("tourism_receipts_fy")
    if len(t) < 2:
        r.missing.append("tourism_receipts_fy (2 years)")
        return no_eval(r)
    r.inputs.append(c.v.latest("tourism_receipts_fy").cite())
    if _war(c) and t.iloc[-1] < t.iloc[-2]:
        fire(r, 1, 0.7)


@rule("EX04")
def ex04(c: Ctx, r: RuleResult):
    p = c.p("EX04")
    gap = c.get("brent_gap", r)
    if gap is None:
        return no_eval(r)
    port = c.v.latest("portfolio_net_fy")
    outflow = (port is not None and port.value < 0) or c.results.get("FX03", RuleResult("", False)).fired
    r.vals.update(brent_gap=gap.value, outflow="portfolio outflow" if outflow else "none")
    if _war(c) and gap.value > p["brent_over_budget"] and outflow:
        fire(r, 1, 1.0)


@rule("EX05")
def ex05(c: Ctx, r: RuleResult):
    p = c.p("EX05")
    s = c.v.series("bop_ca_fy")
    last = c.get("bop_ca_fy", r)
    if last is None or len(s) < 2:
        return no_eval(r)
    ca, prev = s.iloc[-1], s.iloc[-2]
    if ca >= 0 or prev >= 0:
        r.vals.update(widen=0, ca=abs(ca), ca_prev=abs(prev))
        return
    widen = (abs(ca) / abs(prev) - 1) * 100
    r.vals.update(widen=widen, ca=abs(ca), ca_prev=abs(prev))
    if widen > p["widen_pct"]:
        fire(r, 1, min(1.0, widen / 60 + 0.3))


@rule("EX06")
def ex06(c: Ctx, r: RuleResult):
    p = c.p("EX06")
    m = c.get("nir_months_imports", r)
    nir = c.v.series("nir")
    if m is None or nir.empty:
        return no_eval(r)
    record = bool(nir.iloc[-1] >= nir.max())
    r.vals.update(months=m.value, record=" and NIR is at a record high" if record else "",
                  verdict="Above the 5-month floor (tool default).", verdict_ar="ده فوق الحد الأدنى.")
    if m.value < p["min_months"]:
        r.vals.update(verdict="Below 5 months: thin buffer (pressure).", verdict_ar="ده غطاء ضعيف.")
        fire(r, 1, min(1.0, (p["min_months"] - m.value) / 3 + 0.4))
    elif record:
        r.vals.update(verdict="Record reserves: a strong buffer (relief).",
                      verdict_ar="الاحتياطي في أعلى مستوى في تاريخه، وده سند قوي.")
        fire(r, -1, 0.5)


@rule("EX07")
def ex07(c: Ctx, r: RuleResult):
    ev = c.events_of("gulf_deposit_or_megadeal")
    if ev:
        r.inputs += [{"event": e["title_en"], "date": e["event_date"], "url": e["source_url"]} for e in ev]
        r.vals.update(title=ev[0]["title_en"])
        fire(r, -1, min(1.0, max(e["weight_left"] for e in ev)))


# ======================================================================= fiscal & debt
@rule("FD01")
def fd01(c: Ctx, r: RuleResult):
    p = c.p("FD01")
    due = c.events_of("eurobond_maturity_due", within_days=p["eurobond_days"])
    if due:
        r.vals.update(detail=f"Eurobond maturity within {p['eurobond_days']} days ({due[0]['title_en']})",
                      detail_ar="فيه سندات دولية مستحقة خلال شهر")
        return fire(r, 1, 0.5)
    r.missing.append("external debt service due in the next 90 days (MANUAL quarterly schedule)")
    return no_eval(r)


@rule("FD02")
def fd02(c: Ctx, r: RuleResult):
    p = c.p("FD02")
    o = c.get("interest_to_revenue", r, max_level=2)
    if o is None:
        return no_eval(r)
    r.vals.update(ratio=o.value)
    if o.value > p["pct"]:
        fire(r, 1, 0.5)


@rule("FD03")
def fd03(c: Ctx, r: RuleResult):
    p = c.p("FD03")
    end = c.conn.execute("SELECT event_date, source_url FROM calendar WHERE kind='imf' AND event_date>=? ORDER BY event_date LIMIT 1",
                         (c.as_of.isoformat(),)).fetchone()
    reviews = c.events_of("imf_board_approval_disbursement", "imf_staff_level_agreement")
    delays = c.events_of("imf_review_delay")
    if end is None and not reviews:
        r.missing.append("IMF programme calendar/events")
        return no_eval(r)
    if end:
        r.inputs.append({"calendar": "IMF EFF end", "date": end["event_date"], "url": end["source_url"]})
    if delays:
        r.vals.update(detail="IMF review delayed — the anchor is weakening (pressure).",
                      detail_ar="مراجعة صندوق النقد اتأخرت، والسند ده بيضعف.")
        return fire(r, 1, 0.8)
    days_left = (date.fromisoformat(end["event_date"]) - c.as_of).days if end else None
    successor = c.events_of("imf_staff_level_agreement")
    if days_left is not None and days_left <= p["end_watch_days"] and not successor:
        r.vals.update(detail=f"The IMF EFF ends in {days_left} days ({end['event_date']}) with no successor programme announced — watch.",
                      detail_ar=f"برنامج صندوق النقد بيخلص بعد {days_left} يوم ومفيش برنامج جديد متعلن، فلازم نراقب.")
        return fire(r, 1, 0.5)
    recent = [e for e in reviews if (c.as_of - date.fromisoformat(e["event_date"])).days <= p["review_fresh_days"]]
    if recent:
        r.vals.update(detail="IMF programme active and on track (recent review completed) — an anchor for confidence.",
                      detail_ar="برنامج صندوق النقد شغال وماشي في طريقه، وده بيطمن المستثمرين.")
        fire(r, -1, 0.6)
    else:
        r.vals.update(detail="IMF programme active; no recent review event.", detail_ar="برنامج صندوق النقد شغال.")


@rule("FD04")
def fd04(c: Ctx, r: RuleResult):
    p = c.p("FD04")
    ev = [e for e in c.events_of("rating_upgrade", "rating_downgrade", within_days=p["window_days"])]
    if not ev:
        r.vals.update(agency="—", date="—", title="no upgrade/downgrade in the last 60 days", title_ar="")
        return
    e = ev[0]
    r.inputs.append({"event": e["title_en"], "date": e["event_date"], "url": e["source_url"]})
    agency = next((a for a in ("Moody's", "Fitch", "S&P") if a.lower() in e["title_en"].lower()), "Rating agency")
    r.vals.update(agency=agency, date=e["event_date"], title=e["title_en"], title_ar=e["title_ar"])
    fire(r, -1 if e["event_type"] == "rating_upgrade" else 1, 0.6 * e["weight_left"] + 0.2)


@rule("FD05")
def fd05(c: Ctx, r: RuleResult):
    p = c.p("FD05")
    eb, us = c.get("eurobond_yield", r), c.get("us10y", r)
    if eb is None or us is None:
        return no_eval(r)
    spread = (eb.value - us.value) * 100
    r.vals.update(spread=spread, bp=p["bp"])
    if spread > p["bp"]:
        fire(r, 1, min(1.0, spread / 1000))


# ======================================================================= real economy & energy
@rule("RE01")
def re01(c: Ctx, r: RuleResult):
    p = c.p("RE01")
    s = c.v.series("pmi")
    last = c.get("pmi", r)
    if last is None or len(s) < p["months"]:
        return no_eval(r)
    tail = s.iloc[-p["months"]:]
    r.vals.update(months=p["months"], detail=", ".join(f"{d:%b} {v:.1f}" for d, v in tail.items()))
    if (tail < p["level"]).all():
        fire(r, 0, 1.0 if tail.iloc[-1] < p["strong"] else 0.5)


@rule("RE02")
def re02(c: Ctx, r: RuleResult):
    ev = c.events_of("load_shedding_start", "lng_supply_disruption")
    if ev:
        r.inputs += [{"event": e["title_en"], "date": e["event_date"], "url": e["source_url"]} for e in ev]
        r.vals.update(detail=ev[0]["title_en"], detail_ar=ev[0]["title_ar"])
        return fire(r, 1, 0.8)
    r.vals.update(detail="no load-shedding or LNG disruption event active", detail_ar="")


@rule("EC01")
def ec01(c: Ctx, r: RuleResult):
    p = c.p("EC01")
    gap = c.get("brent_gap", r)
    if gap is None:
        return no_eval(r)
    bud = c.v.latest("budget_oil_assumption")
    if bud is None:
        r.missing.append("budget_oil_assumption")
        return no_eval(r)
    r.inputs.append(bud.cite())
    ca = c.v.latest("ca_pressure_pct_gdp")
    r.vals.update(brent=gap.value + bud.value, gap=gap.value, budget=bud.value, ca=ca.value if ca else float("nan"))
    if gap.value > p["gap"]:
        fire(r, 1, 1.0 if gap.value > p["strong"] else 0.4 + 0.6 * (gap.value - p["gap"]) / (p["strong"] - p["gap"]))


@rule("EC02")
def ec02(c: Ctx, r: RuleResult):
    p = c.p("EC02")
    q = c.get("brent_egp_qavg_chg", r)
    if q is None:
        return no_eval(r)
    r.vals.update(chg=q.value)
    freeze = c.events_of("fuel_price_freeze", within_days=90)
    if q.value > p["q_chg_pct"] and freeze:
        r.inputs.append({"event": freeze[0]["title_en"], "date": freeze[0]["event_date"], "url": freeze[0]["source_url"]})
        fire(r, 1, 0.7)


@rule("EC03")
def ec03(c: Ctx, r: RuleResult):
    p = c.p("EC03")
    s = c.v.series("ttf_fut")
    o = c.get("ttf_fut", r)
    if o is None or len(s) < 22:
        m = c.v.series("ttf")
        if len(m) >= 2 and c.v.fresh("ttf"):
            chg = (m.iloc[-1] / m.iloc[-2] - 1) * 100
        else:
            return no_eval(r)
    else:
        chg = _chg(s, 21)
    r.vals.update(chg=chg)
    if chg > p["pct_1m"]:
        fire(r, 1, min(1.0, chg / 60))


@rule("EC04")
def ec04(c: Ctx, r: RuleResult):
    p = c.p("EC04")
    s = c.v.series("wheat")
    o = c.get("wheat", r)
    if o is None or len(s) < 64:
        return no_eval(r)
    chg = _chg(s, 63)
    r.vals.update(chg=chg)
    if chg > p["pct_3m"]:
        fire(r, 1, min(1.0, chg / 40))


@rule("EC05")
def ec05(c: Ctx, r: RuleResult):
    p = c.p("EC05")
    ev = c.events_of("chokepoint_disruption")
    h = c.v.fresh("hormuz_ratio_7dma")
    if h:
        r.inputs.append(h.cite())
    if not ev and h is None:
        r.missing.append("hormuz_ratio_7dma")
        return no_eval(r)
    det, det_ar = [], []
    if ev:
        det.append(f"active event: {ev[0]['title_en']}")
        det_ar.append("فيه حدث تعطيل ملاحة شغال")
    if h and h.value < p["ratio"]:
        det.append(f"Hormuz transits at {h.value:.0%} of the 2023 average")
        det_ar.append(f"حركة السفن في هرمز {h.value * 100:.0f}% بس من متوسط 2023")
    r.vals.update(detail="; ".join(det) or f"Hormuz transits at {h.value:.0%} of 2023", detail_ar="، و".join(det_ar))
    if det:
        fire(r, 1, 0.8)


# ======================================================================= gold & global
@rule("GO01")
def go01(c: Ctx, r: RuleResult):
    g, d = c.v.series("xauusd"), c.v.series("dxy")
    og, od = c.get("xauusd", r), c.get("dxy", r)
    if og is None or od is None or len(g) < 21 or len(d) < 21:
        return no_eval(r)
    cg, cd = _chg(g, 20), _chg(d, 20)
    r.vals.update(gold=cg, dxy=cd)
    if cg > 0 and cd > 0:
        fire(r, 0, 0.5)


@rule("GO02")
def go02(c: Ctx, r: RuleResult):
    p = c.p("GO02")
    s = c.v.series("gold_local_premium_pct")
    if len(s) < p["days"] or c.v.fresh("gold_local_premium_pct") is None:
        r.missing.append(f"gold_local_premium_pct ({p['days']} observations)")
        return no_eval(r)
    tail = s.iloc[-p["days"]:]
    r.inputs.append(c.v.latest("gold_local_premium_pct").cite())
    r.vals.update(days=p["days"], prem=tail.iloc[-1])
    if (tail > p["pct"]).all():
        r.vals.update(sign="premium", verdict="people are hedging against devaluation (pressure).",
                      verdict_ar="الناس بتشتري دهب تحوط من تخفيض الجنيه.")
        fire(r, 1, 0.6)
    elif (tail < -p["pct"]).all():
        r.vals.update(sign="discount", verdict="local dollar demand is easing (relief).",
                      verdict_ar="الطلب المحلي على الدولار بيهدى.")
        fire(r, -1, 0.5)


@rule("GO03")
def go03(c: Ctx, r: RuleResult):
    ng, nf, nir = c.v.series("nir_gold"), c.v.series("nir_fx"), c.v.series("nir")
    if len(ng) < 2 or len(nf) < 2 or len(nir) < 2:
        r.missing.append("nir_gold/nir_fx for two months (MANUAL)")
        return no_eval(r)
    r.vals.update(nir_chg=nir.iloc[-1] - nir.iloc[-2], gold_chg=ng.iloc[-1] - ng.iloc[-2], fx_chg=nf.iloc[-1] - nf.iloc[-2])
    if ng.iloc[-1] - ng.iloc[-2] > 0:
        fire(r, 0, 0.3)


@rule("GL01")
def gl01(c: Ctx, r: RuleResult):
    r.missing.append("FOMC/US CPI consensus (PAID/MANUAL)")
    return no_eval(r)


@rule("GL02")
def gl02(c: Ctx, r: RuleResult):
    p = c.p("GL02")
    vix = c.get("vix", r)
    em = c.v.series("em_spread_proxy")
    if vix is None and len(em) < 22:
        return no_eval(r)
    det, det_ar = [], []
    if vix and vix.value > p["vix"]:
        det.append(f"VIX {vix.value:.1f}")
        det_ar.append("مؤشر الخوف عالي")
    if len(em) >= 22 and c.v.fresh("em_spread_proxy"):
        r.inputs.append(c.v.latest("em_spread_proxy").cite())
        bp = (em.iloc[-1] - em.iloc[-22]) * 100
        if bp > p["spread_bp_1m"]:
            det.append(f"EM spread proxy +{bp:.0f} bp in a month")
            det_ar.append("علاوة المخاطر في الأسواق الناشئة زادت")
    r.vals.update(detail="; ".join(det), detail_ar="، و".join(det_ar))
    if det:
        fire(r, 1, 0.5 * len(det))


@rule("GL03")
def gl03(c: Ctx, r: RuleResult):
    p = c.p("GL03")
    d = c.v.series("dxy")
    fx = c.get("fx_chg_20d", r)
    if fx is None or len(d) < 21 or c.v.fresh("dxy") is None:
        return no_eval(r)
    cd = _chg(d, 20)
    r.vals.update(dxy=cd, fx=fx.value)
    if (abs(cd) > p["pct"] or abs(fx.value) > p["pct"]) and np.sign(cd) != np.sign(fx.value):
        fire(r, 0, 0.3)


@rule("GL04")
def gl04(c: Ctx, r: RuleResult):
    p = c.p("GL04")
    o = c.get("euro_area_pmi", r)
    if o is None:
        return no_eval(r)
    r.vals.update(pmi=o.value)
    if o.value < p["pmi"]:
        fire(r, 1, 0.4)


@rule("GL05")
def gl05(c: Ctx, r: RuleResult):
    p = c.p("GL05")
    det = []
    seen = False
    for sid, name in (("saudi_pmi", "Saudi PMI"), ("uae_pmi", "UAE PMI")):
        o = c.v.fresh(sid)
        if o:
            seen = True
            r.inputs.append(o.cite())
            if o.value < p["pmi"]:
                det.append(f"{name} {o.value:.1f}")
    if not seen:
        r.missing += ["saudi_pmi", "uae_pmi"]
        return no_eval(r)
    r.vals.update(detail=", ".join(det))
    if det:
        fire(r, 1, 0.4 * len(det))


# ======================================================================= geopolitical
@rule("GP01")
def gp01(c: Ctx, r: RuleResult):
    p = c.p("GP01")
    s = c.v.series("gpr_daily")
    o = c.get("gpr_daily", r)
    if o is None or len(s) < 365:
        return no_eval(r)
    win = s[s.index > s.index[-1] - pd.DateOffset(years=p["years"])]
    ma7 = win.rolling(7).mean().dropna()
    p90 = float(np.percentile(ma7, p["pctile"]))
    avg = float(ma7.iloc[-1])
    r.vals.update(avg=avg, p90=p90, pctile=p["pctile"], years=p["years"])
    if avg > p90:
        fire(r, 1, min(1.0, 0.5 + (avg / p90 - 1)))


@rule("GP02")
def gp02(c: Ctx, r: RuleResult):
    p = c.p("GP02")
    s = c.v.series("gpr_egypt")
    o = c.get("gpr_egypt", r)
    if o is None or len(s) < 36:
        return no_eval(r)
    hist = s[s.index > s.index[-1] - pd.DateOffset(years=p["years"])]
    z = (s.iloc[-1] - hist.mean()) / hist.std(ddof=1)
    r.vals.update(val=s.iloc[-1], date=f"{s.index[-1]:%b %Y}", z=z)
    if z > p["std"]:
        fire(r, 1, min(1.0, z / 4))


@rule("GP03")
def gp03(c: Ctx, r: RuleResult):
    p = c.p("GP03")
    tone, vol = c.v.series("gdelt_egypt_economy_tone"), c.v.series("gdelt_egypt_economy_vol")
    ot = c.get("gdelt_egypt_economy_tone", r)
    if ot is None or len(tone) < 30 or len(vol) < 30:
        return no_eval(r)
    t7, v7 = tone.rolling(7).mean().dropna(), vol.rolling(7).mean().dropna()
    zt = (t7.iloc[-1] - t7.mean()) / t7.std(ddof=1)
    zv = (v7.iloc[-1] - v7.mean()) / v7.std(ddof=1)
    r.vals.update(tone=t7.iloc[-1], z=zt)
    if zt < -p["std"] and zv > p["std"]:
        fire(r, 1, 0.5)


@rule("GP04")
def gp04(c: Ctx, r: RuleResult):
    p = c.p("GP04")
    ev = [e for e in c.events if e["domain"] == "geopolitical" and e["direction"] != 0]
    score = sum(e["score"] for e in ev)
    r.vals.update(score=score, n=len(ev))
    r.inputs += [{"event": e["title_en"], "date": e["event_date"], "score": e["score"], "url": e["source_url"]} for e in ev]
    if abs(score) >= p["min_abs"]:
        fire(r, 1 if score > 0 else -1, min(1.0, abs(score) / 5))


# ======================================================================= healthcare
@rule("HC01")
def hc01(c: Ctx, r: RuleResult):
    p = c.p("HC01")
    s = c.v.series("eda_signal")
    o = c.get("eda_signal", r)
    if o is None or len(s) < 2:
        return no_eval(r)
    r.vals.update(sig=s.iloc[-1], pct=p["pct"], days=p["days"])
    if s.iloc[-1] >= p["pct"] and s.iloc[-2] >= p["pct"]:
        fire(r, 0, 0.7)


@rule("HC02")
def hc02(c: Ctx, r: RuleResult):
    p = c.p("HC02")
    s = c.v.series("fx_cbe_official")
    o = c.get("fx_cbe_official", r)
    if o is None:
        return no_eval(r)
    win = s[s.index >= pd.Timestamp(c.as_of - timedelta(days=p["days"]))]
    r.vals.update(level=p["level"], days=p["days"])
    if len(win) >= 20 and (win > p["level"]).all():
        fire(r, 0, 0.6)


@rule("HC03")
def hc03(c: Ctx, r: RuleResult):
    p = c.p("HC03")
    o = c.get("fx_chg_3m", r)
    if o is None:
        return no_eval(r)
    r.vals.update(fx_chg_3m=o.value)
    if o.value > p["pct_3m"]:
        fire(r, 0, 0.5)


# ======================================================================= runner
def _fmt(tpl: str, vals: dict) -> str:
    class F(dict):
        def __missing__(self, k):
            return "—"
    try:
        return tpl.format_map(F(vals))
    except (ValueError, TypeError, KeyError):
        # a missing numeric value in a numeric format spec
        return re.sub(r"\{[^}]*\}", "—", tpl)


def evaluate(conn, as_of: date | None = None, point_in_time: bool = False, base=None) -> dict[str, RuleResult]:
    c = Ctx(conn, as_of, point_in_time, base)
    for rid, fn in RULES.items():
        r = RuleResult(rule_id=rid, evaluable=True)
        try:
            fn(c, r)
        except Exception as e:  # noqa: BLE001
            log.warning("rule %s error: %s", rid, e)
            r.evaluable = False
            r.missing.append(f"error: {e}")
        cfg = c.cfg.get(rid, {})
        if r.evaluable and r.vals:
            r.explanation_en = _fmt(cfg.get("en", ""), r.vals)
            r.explanation_ar = _fmt(cfg.get("ar", ""), r.vals)
            if LATIN.search(r.explanation_ar):  # never let Latin letters into Arabic output
                r.explanation_ar = LATIN.sub("", r.explanation_ar)
        c.results[rid] = r
    return c.results


def evaluate_rules(conn, as_of: date | None = None) -> dict:
    as_of = as_of or today_cairo()
    res = evaluate(conn, as_of)
    cfg = load_yaml("rules.yaml")["rules"]
    conn.execute("DELETE FROM rule_hits WHERE run_date=?", (as_of.isoformat(),))
    for rid, r in res.items():
        conn.execute("INSERT INTO rule_hits VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (as_of.isoformat(), rid, int(r.fired), r.strength, r.direction,
                      to_json({"inputs": r.inputs, "values": r.vals, "missing": r.missing,
                               "affects": cfg.get(rid, {}).get("affects", []), "name": cfg.get(rid, {}).get("name")}),
                      r.explanation_en, r.explanation_ar, cfg.get(rid, {}).get("concept_tag"), int(r.evaluable)))
    conn.commit()
    fired = [k for k, v in res.items() if v.fired]
    log.info("rules: %d evaluated, %d fired (%s), %d not evaluable", sum(v.evaluable for v in res.values()),
             len(fired), ", ".join(fired), sum(not v.evaluable for v in res.values()))
    return {"fired": fired, "results": res}
