"""Weekly deep-dive (Thursday evening): reports/weekly/YYYY-MM-DD.md + .html (SPEC §8.3)."""
from __future__ import annotations

import json
from datetime import date, timedelta

from ..core import REPORTS, today_cairo
from ..data import DataView, catalog
from ..indices import compute
from ..rules import evaluate
from .brief import to_html

CHAINS = {
    "EC01": [("War / supply shock", "حرب أو أزمة إمدادات"), ("Brent ↑", "البترول بيغلى"), ("import bill ↑", "فاتورة الاستيراد بتزيد"),
             ("current-account deficit ↑", "عجز الحساب الجاري بيكبر"), ("pressure on EGP", "ضغط على الجنيه")],
    "EX05": [("Imports grow faster than exports", "الواردات بتزيد أسرع من الصادرات"), ("current-account deficit ↑", "عجز الحساب الجاري بيكبر"),
             ("more dollar demand", "طلب أكتر على الدولار"), ("pressure on EGP unless financed by FDI/portfolio", "ضغط على الجنيه لو مفيش تمويل")],
    "FX04": [("Weak T-bill demand", "طلب ضعيف على أذون الخزانة"), ("yields ↑", "العوايد بتزيد"), ("interest bill ↑", "تكلفة الفوايد بتزيد"),
             ("fiscal stress / crowding out", "ضغط على الموازنة ومزاحمة القطاع الخاص")],
    "EX04": [("War", "حرب"), ("portfolio outflows", "خروج الأموال الساخنة"), ("T-bill yields ↑", "عوايد الأذون بتزيد"),
             ("FX pressure", "ضغط على الجنيه")],
    "MO01": [("Real rate high", "فايدة حقيقية عالية"), ("carry attractive", "المراجحة مربحة"), ("portfolio inflows", "أموال داخلة"),
             ("support for EGP", "دعم للجنيه")],
    "EX01": [("Remittances strong", "تحويلات قوية"), ("dollar supply ↑", "معروض الدولار بيزيد"), ("relief for EGP", "راحة للجنيه")],
    "FD03": [("IMF programme ending", "برنامج صندوق النقد بيخلص"), ("anchor fades", "السند بيضعف"), ("watch for successor", "مستنيين برنامج جديد")],
    "EC02": [("Brent in EGP ↑", "البترول بالجنيه بيغلى"), ("fuel prices frozen", "أسعار الوقود متثبتة"),
             ("deferred hike", "زيادة متأجلة"), ("inflation risk next quarter", "خطر تضخم الربع الجاي")],
}


def write_weekly(conn, as_of: date | None = None) -> str:
    as_of = as_of or today_cairo()
    now = compute(conn, as_of)
    prev_rows = conn.execute("""SELECT index_id, value FROM index_values WHERE run_date<=? AND kind IN ('live','backtest')
                                ORDER BY run_date DESC""", ((as_of - timedelta(days=7)).isoformat(),)).fetchall()
    prev: dict[str, float | None] = {}
    for r in prev_rows:
        prev.setdefault(r["index_id"], r["value"])
    rules = evaluate(conn, as_of)
    top = sorted([r for r in rules.values() if r.fired], key=lambda r: -r.strength)[:5]
    v = DataView(conn, as_of)
    L = [f"# Weekly deep-dive — week ending {as_of.isoformat()}", "",
         "Learning tool, not financial advice. Thresholds/weights are tool defaults.", "",
         "## Summary (English)", ""]
    p = now["ppi"]
    pv = prev.get("PPI")
    L.append(f"- Pound Pressure Index: {p['value'] if p['value'] is not None else 'no data'} "
             f"(coverage {p['coverage_pct']:.0f}%{'' if p['sufficient'] else ', insufficient data'}); "
             f"a week earlier: {pv if pv is not None else 'no stored value'}.")
    L += ["", "| Sub-index | now | 7 days ago | change | coverage |", "|---|---|---|---|---|"]
    for k, s in now["subindices"].items():
        old = prev.get(f"PPI_{k}")
        ch = f"{s['value'] - old:+.1f}" if s["value"] is not None and old is not None else "—"
        L.append(f"| {s['name_en']} | {s['value'] if s['value'] is not None else 'no data'} | "
                 f"{old if old is not None else '—'} | {ch} | {s['coverage_pct']:.0f}% |")
    L += ["", "## Top 5 rules by strength", ""]
    for r in top:
        L.append(f"- **{r.rule_id}** (strength {r.strength:.2f}, {'pressure' if r.direction > 0 else 'relief' if r.direction < 0 else 'note'}): {r.explanation_en}")
    if not top:
        L.append("- No rule fired.")
    L += ["", "## Chains, step by step", ""]
    shown = 0
    for r in top:
        if r.rule_id in CHAINS:
            L.append(f"- {r.rule_id}: " + " → ".join(a for a, _ in CHAINS[r.rule_id]))
            shown += 1
    if not shown:
        L.append("- " + " → ".join(a for a, _ in CHAINS["EC01"]) + " (reference chain)")
    L += ["", "## الملخص بالعربي", ""]
    if p["value"] is not None:
        L.append(f"- مؤشر الضغط على الجنيه {p['value']:+.1f} ونسبة التغطية {p['coverage_pct']:.0f}%.")
    for r in top:
        L.append(f"- {r.explanation_ar}")
    for r in top:
        if r.rule_id in CHAINS:
            L.append("- السلسلة: " + " ← ".join(b for _, b in CHAINS[r.rule_id][::-1]))
    L += ["", "## Data quality", "", "| series | status | latest obs | source |", "|---|---|---|---|"]
    stale, missing = [], []
    for sid, m in catalog().items():
        o = v.latest(sid)
        if o is None:
            missing.append((sid, m["access"]))
        elif o.stale:
            stale.append((sid, "stale" if o.stale == 1 else "very stale (excluded)", o.date, o.source_name))
    for sid, st, d, src in stale:
        L.append(f"| {sid} | {st} | {d} | {src} |")
    L += ["", f"Series with no data at all ({len(missing)}): " + ", ".join(f"{s} ({a})" for s, a in missing)]
    fails = conn.execute("""SELECT source, COUNT(*) n FROM fetch_log WHERE status='error' AND finished_at>=?
                            GROUP BY source""", ((as_of - timedelta(days=7)).isoformat(),)).fetchall()
    L += ["", "Collector failures in the last 7 days: " + (", ".join(f"{r['source']} ×{r['n']}" for r in fails) or "none")]
    md = "\n".join(L) + "\n"
    out = REPORTS / "weekly"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{as_of.isoformat()}.md"
    path.write_text(md, encoding="utf-8")
    (out / f"{as_of.isoformat()}.html").write_text(to_html(md, "Pulse Weekly").replace("dir='rtl'", "dir='ltr'"), encoding="utf-8")
    return str(path)
