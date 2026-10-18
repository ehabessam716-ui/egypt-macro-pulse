"""Daily brief in Egyptian Arabic: briefs/YYYY-MM-DD.md + .html (SPEC §8.2).

Rule: body sentences contain NO Latin letters (numbers allowed). Source URLs go to a numbered
references section after the body; English terms go ONLY to the glossary table at the very end.
"""
from __future__ import annotations

import re
from datetime import date

import markupsafe

from .. import calendar as cal
from ..core import BRIEFS, is_business_day, now_cairo, today_cairo
from ..data import DataView, Obs, catalog
from ..events import active_events, review_queue
from ..indices import compute
from ..rules import evaluate

LATIN = re.compile(r"[A-Za-z]")
BODY_END = "## المراجع"
# Wrap dates, times and signed numbers in Unicode isolates (LRI…PDI) so right-to-left text
# never flips them ("2026-10-18" stays 2026-10-18, "+11.8" stays +11.8).
NUM_RUN = re.compile(r"(?<![\w⁦])([+\-−]?\d[\d,]*(?:\.\d+)?(?:[-:/]\d+)*%?)")


def isolate_numbers(line: str) -> str:
    if line.startswith("|"):
        return line
    head = ""
    m = re.match(r"^(\s*(?:#+|-|\d+\.)\s)", line)
    if m and not line.lstrip().startswith(("- ", "#")):
        return line
    if m:
        head, line = m.group(1), line[len(m.group(1)):]
    return head + NUM_RUN.sub(lambda x: "⁦" + x.group(1) + "⁩", line)

SOURCE_AR = {
    "cbe": "البنك المركزي المصري", "yahoo_markets": "ياهو فاينانس (غير رسمي)", "fred_csv": "قاعدة بيانات فيد سانت لويس",
    "portwatch_chokepoints": "مرصد الموانئ بصندوق النقد الدولي", "gpr_monthly": "مؤشر كالدارا وياكوفيلو",
    "gpr_daily": "مؤشر كالدارا وياكوفيلو", "gold_banklive": "موقع بنك لايف", "gold_isagha": "موقع آي صاغة",
    "sp_pmi": "ستاندرد آند بورز جلوبال", "derived": "حسابات الأداة", "imf_datamapper": "صندوق النقد الدولي",
    "worldbank_api": "البنك الدولي", "eurostat_hicp": "مكتب الإحصاء الأوروبي", "gdelt_doc": "قاعدة أخبار جيدلت",
    "manual": "مصدر صحفي", "capmas": "مصدر صحفي نقلا عن جهاز الإحصاء",
}
UNIT_AR = {"EGP per USD": "جنيه للدولار", "%": "%", "pp": "نقطة مئوية", "USD mn": "مليون دولار", "USD bn": "مليار دولار",
           "USD/bbl": "دولار للبرميل", "EGP/gram": "جنيه للجرام", "USD/oz": "دولار للأوقية", "index": "نقطة",
           "ratio": "", "months": "شهور", "EGP/litre": "جنيه للتر", "% GDP": "% من الناتج", "EGP/bbl": "جنيه للبرميل"}
KIND_AR = {"mpc": "اجتماع لجنة السياسة النقدية في البنك المركزي", "fomc": "قرار الفايدة الأمريكية",
           "cpi": "أرقام التضخم من جهاز الإحصاء (متوقع)", "core_cpi": "التضخم الأساسي من البنك المركزي (متوقع)",
           "pmi": "مؤشر مديري المشتريات (متوقع)", "nir": "أرقام الاحتياطي (متوقع)", "gpr": "تحديث مؤشر المخاطر الشهري",
           "gpr_daily": "تحديث مؤشر المخاطر اليومي", "portwatch": "تحديث بيانات حركة السفن",
           "imf": "نهاية برنامج صندوق النقد", "fuel_committee": "لجنة تسعير الوقود (غير مؤكد)",
           "eda": "أول نافذة لإعادة تسعير الدواء (تقدير صحفي)"}
SUB_AR = {"external": "القطاع الخارجي", "monetary": "الفايدة والأسواق", "fiscal": "المالية العامة والديون",
          "commodities": "السلع والطاقة", "geopolitical": "السياسة والمنطقة", "global": "العالم وأمريكا"}

GLOSSARY = [
    ("مؤشر الضغط على الجنيه", "Pound Pressure Index (PPI)", "رقم من سالب 100 لموجب 100، الموجب معناه ضغط على الجنيه"),
    ("نسبة التغطية", "Coverage", "نسبة البيانات الحديثة اللي دخلت في حساب المؤشر"),
    ("الفايدة الحقيقية", "Real interest rate", "الفايدة ناقص التضخم"),
    ("عائد المراجحة", "Carry trade", "تستلف بعملة فايدتها قليلة وتستثمر في عملة فايدتها عالية"),
    ("انتقال أثر سعر الصرف", "Exchange-rate pass-through", "غلو الدولار بيعدي على أسعار السلع"),
    ("التضخم الأساسي", "Core inflation", "التضخم من غير الأكل الطازة والسلع المسعرة إداريا"),
    ("صافي الاحتياطيات الدولية", "Net international reserves (NIR)", "الدولارات والدهب اللي في إيد البنك المركزي"),
    ("الحساب الجاري", "Current account", "صافي التجارة والخدمات والتحويلات والدخل مع العالم"),
    ("الأموال الساخنة", "Hot money / portfolio flows", "استثمارات أجنبية قصيرة الأجل بتدخل وتخرج بسرعة"),
    ("تكلفة التأمين على الديون", "CDS (credit default swap)", "تمن التأمين ضد إن الدولة متدفعش ديونها"),
    ("مؤشر مديري المشتريات", "PMI", "استطلاع لنشاط القطاع الخاص، فوق 50 يعني نمو"),
    ("مؤشر المخاطر الجيوسياسية", "Geopolitical Risk index (GPR)", "بيعد الأخبار عن الحروب والتوترات"),
    ("السعر الموازي", "Parallel market rate", "سعر الدولار برة البنوك"),
    ("دولار الدهب", "Gold-implied exchange rate", "سعر الدولار المحسوب من سعر الدهب المحلي والعالمي"),
    ("الآثار التانية", "Second-round effects", "لما زيادة سعر حاجة واحدة تزود أسعار حاجات تانية"),
    ("حدث متضاءل", "Event decay / half-life", "أثر الحدث بيقل للنص كل فترة ثابتة"),
]


class Refs:
    def __init__(self):
        self.items: list[tuple[str, str]] = []

    def num(self, name: str, url: str) -> int:
        for i, (n, u) in enumerate(self.items, 1):
            if u == url:
                return i
        self.items.append((name, url))
        return len(self.items)


def src_ar(o: Obs) -> str:
    key = catalog().get(o.series_id, {}).get("source", "")
    if key.startswith("cbe"):
        key = "cbe"
    if o.quality == "secondary" and not key.startswith("gold"):
        return "مصدر صحفي"
    return SOURCE_AR.get(key, "مصدر خارجي")


class Writer:
    def __init__(self, v: DataView, refs: Refs):
        self.v, self.refs = v, refs

    def cite(self, o: Obs) -> str:
        if o.source_url.startswith("pulse/"):
            n = self.refs.num("Egypt Macro Pulse — " + o.source_url, "pulse/derive.py")
        else:
            n = self.refs.num(o.source_name, o.source_url)
        flag = "، قديم شوية" if o.stale == 1 else ("، قديم جدا" if o.stale == 2 else "")
        return f"(المصدر: {src_ar(o)} [{n}]، بتاريخ {o.date.isoformat()}{flag})"

    def val(self, sid: str, digits: int = 2, unit: str | None = None, sign: bool = False) -> str | None:
        o = self.v.latest(sid)
        if o is None:
            return None
        u = UNIT_AR.get(catalog()[sid].get("unit"), "") if unit is None else unit
        fmtd = f"{o.value:+,.{digits}f}" if sign else f"{o.value:,.{digits}f}"
        return f"{fmtd} {u}".strip() + " " + self.cite(o)

    def line(self, label: str, sid: str, digits: int = 2, unit: str | None = None, sign: bool = False) -> str:
        v = self.val(sid, digits, unit, sign)
        return f"- {label}: {v}" if v else f"- {label}: مفيش بيانات"


def build_brief(conn, as_of: date | None = None) -> str:
    as_of = as_of or today_cairo()
    v = DataView(conn, as_of)
    refs = Refs()
    w = Writer(v, refs)
    idx = compute(conn, as_of)
    rules = evaluate(conn, as_of)
    fired = sorted([r for r in rules.values() if r.fired], key=lambda r: -r.strength)
    L: list[str] = [f"# نبض الاقتصاد المصري — موجز يوم {as_of.isoformat()}", ""]
    L.append("أداة تعليمية مش نصيحة استثمارية. كل رقم معاه مصدره وتاريخه، والأرقام الناقصة مكتوب قدامها مفيش بيانات.")
    if not is_business_day(as_of, "egypt"):
        L.append("النهارده إجازة البنوك في مصر، فالأسعار الرسمية هي آخر سعر اتنشر بتاريخه (سوق مقفول).")
    L += ["", "## الخلاصة", ""]
    p = idx["ppi"]
    if p["value"] is None:
        L.append("- مؤشر الضغط على الجنيه: مفيش بيانات كفاية النهارده.")
    else:
        mood = "ضغط على الجنيه" if p["value"] > 10 else ("راحة للجنيه" if p["value"] < -10 else "الوضع متوازن تقريبا")
        suff = "" if p["sufficient"] else " لكن البيانات مش كفاية فالرقم ده استرشادي بس"
        n = refs.num("Egypt Macro Pulse — PPI (config/indices.yaml)", "pulse/indices.py")
        L.append(f"- مؤشر الضغط على الجنيه {p['value']:+.1f} من 100 ({mood})، ونسبة التغطية {p['coverage_pct']:.0f}%{suff} "
                 f"(المصدر: حسابات الأداة [{n}]، بتاريخ {as_of.isoformat()}).")
    for k, s in idx["subindices"].items():
        if s["value"] is not None:
            L.append(f"- مؤشر {SUB_AR[k]}: {s['value']:+.0f} (تغطية {s['coverage_pct']:.0f}%)")
    if fired:
        L.append("- أهم الإشارات النهارده:")
        for r in fired[:3]:
            L.append(f"  - {r.explanation_ar}")
    L += ["", "## الجنيه النهارده", ""]
    L.append(w.line("سعر الدولار الرسمي (شراء)", "fx_cbe_official", 4))
    L.append(w.line("تغير الدولار في 20 يوم عمل", "fx_chg_20d", 2, "%", sign=True))
    L.append(w.line("سعر الدولار في السوق العالمي", "fx_market", 2))
    L.append(w.line("دولار الدهب", "fx_gold_implied", 2))
    L.append(w.line("الفرق بين دولار الدهب والرسمي", "gold_gap_pct", 2, "%", sign=True))
    L.append(w.line("عائد أذون الخزانة لسنة", "tbill_12m_yield", 2))
    for rid in ("FX02", "FX04", "FX05", "FX01"):
        r = rules.get(rid)
        if r and r.fired:
            L.append(f"- {r.explanation_ar}")
    L += ["", "## الفلوس الداخلة والخارجة", ""]
    L.append(w.line("صافي الاحتياطيات الدولية", "nir", 1))
    L.append(w.line("تحويلات المصريين بالخارج في آخر شهر", "remittances", 1))
    L.append(w.line("نمو التحويلات السنوي", "remittances_yoy", 1, "%", sign=True))
    L.append(w.line("عجز الحساب الجاري في السنة المالية", "bop_ca_fy", 1))
    L.append(w.line("حركة قناة السويس مقارنة بسنة 2023 (نسبة)", "suez_ratio_7dma", 2, ""))
    L.append(w.line("إيرادات السياحة في السنة المالية", "tourism_receipts_fy", 1))
    L.append(w.line("الاحتياطي يغطي كام شهر واردات", "nir_months_imports", 1))
    for rid in ("EX01", "EX02", "EX05", "EX06"):
        r = rules.get(rid)
        if r and r.fired:
            L.append(f"- {r.explanation_ar}")
    L += ["", "## الفايدة والتضخم", ""]
    L.append(w.line("فايدة الإيداع لليلة واحدة", "cbe_odr", 2))
    L.append(w.line("التضخم السنوي في المدن", "cpi_urban_yoy", 1))
    L.append(w.line("التضخم الأساسي السنوي", "cpi_core_yoy", 1))
    L.append(w.line("الفايدة الحقيقية", "real_headline", 1, sign=True))
    for rid in ("MO01", "MO04", "MO05", "MO06", "MO07"):
        r = rules.get(rid)
        if r and r.fired:
            L.append(f"- {r.explanation_ar}")
    L += ["", "## البترول والدهب", ""]
    L.append(w.line("خام برنت الفوري", "brent", 2))
    L.append(w.line("عقود برنت الآجلة", "brent_fut", 2))
    L.append(w.line("سعر البترول في الموازنة", "budget_oil_assumption", 0))
    L.append(w.line("سعر بنزين 92", "fuel_92", 2))
    L.append(w.line("جرام الدهب عيار 21", "gold_eg_21k", 0))
    L.append(w.line("أوقية الدهب العالمية", "xauusd", 0))
    for rid in ("EC01", "EC02", "GO02"):
        r = rules.get(rid)
        if r and r.fired:
            L.append(f"- {r.explanation_ar}")
    L += ["", "## السياسة والمنطقة", ""]
    L.append(w.line("مؤشر المخاطر الجيوسياسية اليومي", "gpr_daily", 0))
    L.append(w.line("مؤشر المخاطر الجيوسياسية لمصر", "gpr_egypt", 2))
    L.append(w.line("حركة مضيق هرمز مقارنة بسنة 2023 (نسبة)", "hormuz_ratio_7dma", 2, ""))
    for e in active_events(conn, as_of, include_tags=True)[:8]:
        n = refs.num(e["source_name"], e["source_url"])
        conf = "مؤكد" if e["confidence"] == "confirmed" else "منشور في أكتر من مصدر"
        L.append(f"- {e['title_ar']} ({conf}، [{n}]، بتاريخ {e['event_date']})")
    q = review_queue(conn)
    if q:
        L.append(f"- فيه {len(q)} أحداث مقترحة من الأخبار مستنية مراجعة، ومش داخلة في الحسابات.")
    L += ["", "## إيه اللي جاي في الأجندة", ""]
    items = [c for c in cal.upcoming(conn, 14) if c["kind"] in KIND_AR]
    if not items:
        L.append("- مفيش مواعيد مهمة في الأسبوعين الجايين.")
    for c in items:
        n = refs.num(c["description"], c["source_url"])
        t = f" الساعة {c['event_time_cairo']}" if c.get("event_time_cairo") else ""
        L.append(f"- {c['event_date']}{t}: {KIND_AR[c['kind']]} [{n}]")
    # body ends here — everything below may contain Latin letters (URLs, English terms)
    L += ["", BODY_END, ""]
    for i, (name, url) in enumerate(refs.items, 1):
        L.append(f"{i}. {name} — {url}")
    L += ["", "## قاموس المصطلحات", "", "| المصطلح بالعربي | English term | شرح بسيط |", "|---|---|---|"]
    for ar, en, ex in GLOSSARY:
        L.append(f"| {ar} | {en} | {ex} |")
    text = "\n".join(L) + "\n"
    body = text.split(BODY_END)[0]
    # safety net: never ship Latin letters in the body
    clean = []
    for line in body.splitlines():
        line = LATIN.sub("", line) if LATIN.search(line) else line
        clean.append(isolate_numbers(line))
    return "\n".join(clean).rstrip("\n") + "\n\n" + BODY_END + text.split(BODY_END, 1)[1]


def body_of(text: str) -> str:
    return text.split(BODY_END)[0]


def to_html(md: str, title: str) -> str:
    import html as _h
    out = []
    in_table = False
    for line in md.splitlines():
        e = _h.escape(line)
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-"):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            out.append("<tr>" + "".join(f"<td>{_h.escape(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if line.startswith("# "):
            out.append(f"<h1>{e[2:]}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{e[3:]}</h2>")
        elif line.startswith("  - "):
            out.append(f"<p class='sub'>• {e[4:]}</p>")
        elif line.startswith("- "):
            out.append(f"<p>• {e[2:]}</p>")
        elif re.match(r"\d+\. ", line):
            num, rest = line.split(". ", 1)
            url = rest.rsplit(" — ", 1)[-1]
            link = f"<a href='{_h.escape(url)}' dir='ltr'>{_h.escape(rest)}</a>" if url.startswith("http") else f"<span dir='ltr'>{_h.escape(rest)}</span>"
            out.append(f"<p class='ref'>{num}. {link}</p>")
        elif line.strip():
            out.append(f"<p>{e}</p>")
    if in_table:
        out.append("</table>")
    css = ("body{margin:0;background:#fcfcfb;color:#0b0b0b;font:16px/1.8 'Noto Naskh Arabic','Segoe UI',Tahoma,sans-serif}"
           "main{max-width:820px;margin:0 auto;padding:16px}h1{font-size:22px}h2{font-size:18px;margin-top:26px}"
           "p{margin:6px 0}.sub{margin-right:18px}.ref{font-size:13px;direction:ltr;text-align:left}"
           "table{border-collapse:collapse;width:100%;font-size:14px}td{border-bottom:1px solid #e2e1dc;padding:6px}"
           "a{color:#2a78d6;word-break:break-all}"
           "@media (prefers-color-scheme:dark){body{background:#1a1a19;color:#f0efec}td{border-color:#383835}a{color:#3987e5}}")
    return (f"<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width, initial-scale=1'><title>{markupsafe.escape(title)}</title><style>{css}</style>"
            f"</head><body><main>{''.join(out)}</main></body></html>")


def write_brief(conn, as_of: date | None = None) -> str:
    as_of = as_of or today_cairo()
    md = build_brief(conn, as_of)
    BRIEFS.mkdir(parents=True, exist_ok=True)
    path = BRIEFS / f"{as_of.isoformat()}.md"
    path.write_text(md, encoding="utf-8")
    (BRIEFS / f"{as_of.isoformat()}.html").write_text(to_html(md, "Pulse Brief"), encoding="utf-8")
    return str(path)
