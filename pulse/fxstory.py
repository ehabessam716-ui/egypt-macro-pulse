"""'Why is the dollar moving?' — a plain-language explainer built only from tracked numbers.

Every fact carries its source and date. Causes are *signals consistent with* the move, not proof; the
"what usually happens next" and "what can slow it" parts are the standard policy playbook, not forecasts.
Thresholds are tool defaults.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from .data import DataView

WINDOW_DAYS = 14
POLITICAL = ("israel", "gaza", "iran", "houthi", "red sea", "sudan", "libya", "hezbollah", "yemen",
             "west bank", "sinai", "rafah", "hamas", "missile", "airstrike", "ceasefire", "escalat",
             "إسرائيل", "غزة", "إيران", "الحوثي", "البحر الأحمر", "السودان", "ليبيا", "اليمن", "رفح", "سيناء")


def _src(o, name=None):
    return {"name": name or o.source_name, "url": o.source_url, "date": o.date.isoformat()}


def _pct(a, b):
    return (a / b - 1) * 100 if a is not None and b else None


def _f(x, d=2):
    return f"{x:,.{d}f}"


DEAL_SIZE = 3000.0  # EGP mn — single sessions above this usually include one-off block deals / bond trades


def hot_money(v: DataView) -> dict:
    """Shared hot-money assessment: foreign flows, stocks in dollars, CIB London gap vs its own norm, T-bill demand.
    status: 1 = money leaving (hurting the pound), -1 = coming in, 0 = no clear signal. Thresholds are tool defaults."""
    sig_out, sig_in, fe, fa, src = 0, 0, [], [], []
    headline = None
    fl = v.series("egx_foreign_net")
    if len(fl) >= 3:
        last = fl.iloc[-5:]
        tot, sells = float(last.sum()), int((last < 0).sum())
        big = int((last.abs() > DEAL_SIZE).sum())
        o = v.latest("egx_foreign_net")
        fe.append(f"foreign investors were net sellers in {sells} of the last {len(last)} EGX sessions, a net {tot / 1000:+.1f}bn pounds"
                  + (f" ({big} of those sessions were above EGP 3bn and may include one-off deals)" if big else "")
                  + f"; latest {o.value / 1000:+.2f}bn on {o.date:%d %b}")
        fa.append(f"الأجانب كانوا صافي بايعين في {sells} من آخر {len(last)} جلسات في البورصة، بصافي {tot / 1000:+.1f} مليار جنيه"
                  + (f" ({big} جلسات منهم فوق 3 مليار وممكن يكون فيها صفقات استثنائية)" if big else "")
                  + f"، وآخر جلسة {o.value / 1000:+.2f} مليار")
        sig_out += sells >= 3 and tot < 0
        sig_in += sells <= 1 and tot > 0
        src.append(_src(o, "EGX foreign net flows (market reports)"))
        headline = (f"{tot / 1000:+.1f}bn / 5 sessions", f"{tot / 1000:+.1f} مليار / 5 جلسات")
    tb = v.latest("tbill_foreign_net")
    if tb and (date.today() - tb.date).days <= 14:
        fe.append(f"foreigners {'sold' if tb.value < 0 else 'bought'} a net EGP {abs(tb.value) / 1000:.1f}bn of T-bills ({tb.date:%d %b})")
        fa.append(f"الأجانب {'باعوا' if tb.value < 0 else 'اشتروا'} أذون خزانة بصافي {abs(tb.value) / 1000:.1f} مليار جنيه")
        sig_out += tb.value < 0
        sig_in += tb.value > 0
        src.append(_src(tb, "T-bill foreign flows (press)"))
    es = v.series("egx30_usd")
    if len(es) > 60:
        ch10 = es.pct_change(10).dropna() * 100
        now, pctl = float(ch10.iloc[-1]), float((ch10 < ch10.iloc[-1]).mean() * 100)
        fe.append(f"Egyptian stocks measured in dollars moved {now:+.1f}% over 10 sessions — " +
                  (f"worse than {100 - pctl:.0f}% of all 10-session periods since {es.index[0]:%Y}" if pctl <= 50 else f"better than {pctl:.0f}% of past periods"))
        fa.append(f"البورصة بالدولار اتحركت {now:+.1f}% في 10 جلسات، " +
                  (f"وده أسوأ من {100 - pctl:.0f}% من كل الفترات من {es.index[0]:%Y}" if pctl <= 50 else f"وده أحسن من {pctl:.0f}% من الفترات اللي فاتت"))
        sig_out += pctl <= 10
        sig_in += pctl >= 90
        src.append(_src(v.latest("egx30_usd"), "EGX30 in USD (derived)"))
    pm = v.series("cib_gdr_premium_pct")
    if len(pm) > 60:
        med = float(pm[pm.index >= pm.index[-1] - pd.Timedelta(days=90)].median())
        dev = float(pm.iloc[-1]) - med
        fe.append(f"CIB's London price implies a dollar {pm.iloc[-1]:+.1f}% above Cairo vs a usual {med:+.1f}% (90-day median)" +
                  (" — foreigners are pricing a weaker pound" if dev > 1.5 else " — normal, no extra stress"))
        fa.append(f"سعر التجاري الدولي في لندن بيدي دولار أعلى من القاهرة بـ {pm.iloc[-1]:+.1f}% مقابل {med:+.1f}% في العادي" +
                  (" يعني الأجانب متوقعين جنيه أضعف" if dev > 1.5 else " يعني طبيعي ومفيش ضغط زيادة"))
        sig_out += dev > 1.5
        sig_in += dev < -1.5
        src.append(_src(v.latest("cib_gdr_premium_pct"), "CIB London GDR vs Cairo (derived)"))
    bt, yl = v.series("tbill_3m_btc"), v.series("tbill_3m_yield")
    if len(bt) >= 5 and len(yl) >= 5:
        b_now, b_prev = float(bt.iloc[-1]), float(bt.iloc[-5:-1].mean())
        y_now, y_prev = float(yl.iloc[-1]), float(yl.iloc[-5])
        fe.append(f"demand at the 3-month T-bill auction was {b_now:.1f}× the offer vs {b_prev:.1f}× before, yield {y_prev:.2f}% → {y_now:.2f}%")
        fa.append(f"الطلب على أذون 3 شهور كان {b_now:.1f} مرة قد المعروض مقابل {b_prev:.1f} قبلها، والعائد من {y_prev:.2f}% لـ {y_now:.2f}%")
        sig_out += b_now < 0.8 * b_prev
        src.append(_src(v.latest("tbill_3m_btc"), "CBE T-bill auctions"))
    strength = "strong" if sig_out >= 2 else "some" if sig_out == 1 else "none"
    status = 1 if sig_out >= 2 else (-1 if sig_in >= 2 and sig_out == 0 else 0)
    return {"status": status, "strength": strength, "signals_out": sig_out, "signals_in": sig_in,
            "facts_en": fe, "facts_ar": fa, "sources": src, "headline": headline}


def build_fx_story(v: DataView, quotes: list[dict], cbe: dict | None, mid: dict | None, news: list[dict]) -> dict | None:
    today = date.today()
    start_d = today - timedelta(days=WINDOW_DAYS)
    o0 = v.value_at("fx_cbe_official", start_d)
    ol = v.latest("fx_cbe_official")
    if not o0 or not ol:
        return None
    now_v, now_date = (cbe["buy"], cbe["date"]) if cbe else (ol.value, ol.date.isoformat())
    move = _pct(now_v, o0.value)
    direction = "up" if move >= 1 else "down" if move <= -1 else "flat"
    days = (date.fromisoformat(now_date) - o0.date).days
    cbe_src = {"name": "Central Bank of Egypt — exchange rates", "url": o0.source_url, "date": now_date}

    why = []

    def item(iid, icon, strength, title, text, sources):
        why.append({"id": iid, "icon": icon, "strength": strength, "title": title, "text": text, "sources": sources})

    # 1) politics / war risk
    g = v.latest("gpr_daily")
    gs = v.series("gpr_daily")
    if g is not None and len(gs) > 30:
        base = float(gs[gs.index >= pd.Timestamp(g.date - timedelta(days=365))].mean())
        ratio = g.value / base if base else None
        peak = float(gs[gs.index >= pd.Timestamp(start_d)].max()) if (gs.index >= pd.Timestamp(start_d)).any() else g.value
        pr = peak / base if base else 0
        st = "strong" if pr >= 1.6 else "some" if pr >= 1.25 else "none"
        pol = [n for n in (news or []) if any(k in (n.get("title") or "").lower() for k in POLITICAL)]
        item("politics", "⚔", st, ["Political & war risk", "المخاطر السياسية والحروب"],
             [f"The daily geopolitical-risk index peaked at {_f(peak, 0)} in the last two weeks — {pr:.1f}× its 12-month average ({_f(base, 0)}); latest {_f(g.value, 0)} on {g.date:%d %b}. "
              + ("When risk jumps like this, foreign investors usually pull 'hot money' out of emerging markets first and ask questions later." if st != "none"
                 else "That is not unusual, so politics is not the main driver right now."),
              f"مؤشر المخاطر الجيوسياسية اليومي وصل لـ {_f(peak, 0)} في آخر أسبوعين، يعني {pr:.1f} ضعف متوسط السنة ({_f(base, 0)})، وآخر قراءة {_f(g.value, 0)}. "
              + ("ولما المخاطر تقفز كده، المستثمر الأجنبي غالبا بيسحب الأموال الساخنة من الأسواق الناشئة الأول وبعدين يسأل." if st != "none"
                 else "وده مش غير عادي، يعني السياسة مش السبب الأساسي دلوقتي.")],
             [_src(g, "Caldara & Iacoviello GPR (daily)")] + [{"name": n["outlet"] + ": " + n["title"][:70], "url": n["url"], "date": n["at"][:10]} for n in pol[:3]])

    # 2) hot money — one shared assessment (also drives the chain box)
    hm = hot_money(v)
    if hm["facts_en"]:
        st = hm["strength"]
        item("hot_money", "⇅", st, ["Hot money leaving", "خروج الأموال الساخنة"],
             ["; ".join(hm["facts_en"]) + ". " + ("Together these point to foreign portfolio money ('hot money') leaving — each exit means selling pounds for dollars."
                                                    if st != "none" else "These do not show a clear foreign exit."),
              "، و".join(hm["facts_ar"]) + ". " + ("وده كله بيقول إن الأموال الساخنة (استثمارات الأجانب قصيرة المدى) بتخرج، وكل خروج معناه بيع جنيه وشرا دولار."
                                                    if st != "none" else "ومفيش علامة واضحة على خروج الأجانب.")],
             hm["sources"])

    # 3) global dollar
    dx0, dxl = v.value_at("dxy", start_d), v.latest("dxy")
    if dx0 and dxl:
        ch = _pct(dxl.value, dx0.value)
        st = "some" if ch >= 1 else "none"
        item("global_usd", "◎", st, ["The dollar worldwide", "الدولار عالميا"],
             [f"The US dollar index moved {ch:+.1f}% over the same period — " + ("a stronger dollar everywhere adds a little pressure." if st != "none" else "so this is an Egypt-specific move, not a global dollar rally."),
              f"مؤشر الدولار العالمي اتحرك {ch:+.1f}% في نفس الفترة، " + ("والدولار القوي في كل حتة بيزود الضغط شوية." if st != "none" else "يعني الحركة دي خاصة بمصر مش ارتفاع عالمي للدولار.")],
             [_src(dxl, "ICE US Dollar Index (Yahoo)")])

    # 4) oil import bill
    br, bud = v.latest("brent_fut"), v.latest("budget_oil_assumption")
    if br and bud:
        gap = _pct(br.value, bud.value)
        st = "some" if gap > 20 else "none"
        item("oil", "⛽", st, ["Expensive oil", "البترول الغالي"],
             [f"Brent is ${br.value:.0f} vs ${bud.value:.0f} in the budget ({gap:+.0f}%). Egypt imports fuel, so pricier oil means more dollars leaving every month — a steady background pressure rather than a sudden trigger.",
              f"برنت بـ {br.value:.0f} دولار مقابل {bud.value:.0f} في الموازنة ({gap:+.0f}%). ومصر بتستورد وقود، فالبترول الغالي معناه دولارات أكتر خارجة كل شهر، ضغط مستمر في الخلفية مش سبب مفاجئ."],
             [_src(br, "Brent futures (Yahoo)"), _src(bud, "Ministry of Finance budget")])

    # 5) households: gold-implied rate (panic check)
    gi, off = v.latest("fx_gold_implied"), now_v
    if gi:
        gap = _pct(gi.value, off)
        st = "strong" if gap > 5 else "some" if gap > 3 else "none"
        item("households", "💰", st, ["People rushing to gold", "الناس بتجري على الدهب"],
             [f"The dollar rate implied by local gold prices is {gi.value:.2f} ({gap:+.1f}% vs official). " + ("Households are paying extra to protect savings." if st != "none" else "Within ±3% — no sign of panic buying at home."),
              f"دولار الدهب {gi.value:.2f} ({gap:+.1f}% عن الرسمي). " + ("الناس بتدفع زيادة عشان تحمي فلوسها." if st != "none" else "جوه حدود ±3%، يعني مفيش هلع جوه البلد.")],
             [_src(gi, "Gold-implied USD/EGP (derived)")])

    order = {"strong": 0, "some": 1, "none": 2}
    why.sort(key=lambda x: order[x["strength"]])
    main = [w for w in why if w["strength"] != "none"]

    # what if it continues (standard transmission; numbers are today's levels)
    cpi, nir, nirm = v.latest("cpi_urban_yoy"), v.latest("nir"), v.latest("nir_months_imports")
    cont = [
        ["Imported goods get pricier within weeks (fuel, wheat, medicine, electronics), so inflation" + (f" — {cpi.value:.1f}% in {cpi.date:%b %Y} —" if cpi else "") + " may stop falling.",
         "المستورد يغلى خلال أسابيع (وقود، قمح، أدوية، أجهزة)، فالتضخم" + (f" ({cpi.value:.1f}% في {cpi.date:%m/%Y})" if cpi else "") + " ممكن يبطّل ينزل."],
        ["The government pays more pounds for its dollar debt and fuel imports, squeezing the budget.",
         "الحكومة بتدفع جنيهات أكتر في ديونها بالدولار واستيراد الوقود، والموازنة بتتضغط."],
        ["Savers move into dollars and gold, which can feed the move — watch the gold-implied rate.",
         "الناس بتحول مدخراتها لدولار ودهب، وده ممكن يزود الحركة، راقب دولار الدهب."],
        ["Reserves are the shock absorber" + (f": ${nir.value / 1000:.1f}bn" + (f" (~{nirm.value:.1f} months of imports)" if nirm else "") if nir else "") + ", so a disorderly fall is less likely than in 2022–23.",
         "الاحتياطي هو المخدة" + (f": {nir.value / 1000:.1f} مليار دولار" + (f" (حوالي {nirm.value:.1f} شهور استيراد)" if nirm else "") if nir else "") + "، فاحتمال انهيار عشوائي أقل من 2022 و2023."],
    ]
    if direction != "up":
        cont = []

    # levers: what usually slows a drain (playbook, with today's settings)
    odr, real, y3 = v.latest("cbe_odr"), v.latest("real_headline"), v.latest("tbill_3m_yield")
    mpc = None
    try:
        r = v.conn.execute("select event_date from calendar where kind='mpc' and event_date>=? order by event_date limit 1", (today.isoformat(),)).fetchone()
        mpc = r[0] if r else None
    except Exception:  # noqa: BLE001
        pass
    levers = [
        {"icon": "🏦", "title": ["Higher T-bill yields (fastest)", "عائد أعلى على أذون الخزانة (الأسرع)"],
         "text": ["At the weekly auctions the Finance Ministry and CBE can accept higher yields so holding pounds pays more — the quickest way to stop hot money leaving.",
                  "في المزادات الأسبوعية وزارة المالية والبنك المركزي ممكن يقبلوا عائد أعلى، فالاحتفاظ بالجنيه يكسب أكتر، وده أسرع طريقة توقف خروج الأموال الساخنة."],
         "now": [f"3-month yield {y3.value:.2f}% ({y3.date:%d %b})", f"عائد 3 شهور {y3.value:.2f}%"] if y3 else None},
        {"icon": "%", "title": ["Raise the policy rate", "رفع سعر الفايدة"],
         "text": ["The Monetary Policy Committee can raise rates to defend the pound. It is a strong signal, but it also slows the economy and raises the government's interest bill.",
                  "لجنة السياسة النقدية ممكن ترفع الفايدة عشان تحمي الجنيه. دي إشارة قوية بس بتبطّأ الاقتصاد وبتزود فوايد ديون الحكومة."],
         "now": ([f"deposit rate {odr.value:.2f}%" + (f", real rate {real.value:+.1f}% above inflation" if real else "") + (f" · next meeting {mpc}" if mpc else ""),
                  f"فايدة الإيداع {odr.value:.2f}%" + (f"، أعلى من التضخم بـ {real.value:+.1f}%" if real else "") + (f" · الاجتماع الجاي {mpc}" if mpc else "")] if odr else None)},
        {"icon": "⇄", "title": ["Let the pound flex", "سيب الجنيه يتحرك"],
         "text": ["Under the flexible exchange rate, a cheaper pound itself attracts buyers back (exporters, tourists, investors) — the move can stop once the price looks good enough.",
                  "مع سعر الصرف المرن، الجنيه الأرخص بنفسه بيرجّع المشترين (المصدرين والسياح والمستثمرين)، والحركة ممكن تقف لما السعر يبقى مغري."],
         "now": None},
        {"icon": "🛡", "title": ["Use reserves & swap lines", "استخدام الاحتياطي"],
         "text": ["The CBE and banks can supply dollars from reserves to smooth sharp days. It calms the market but is limited and costly if the outflow lasts.",
                  "البنك المركزي والبنوك ممكن يضخوا دولارات من الاحتياطي في الأيام الصعبة. ده بيهدّي السوق بس محدود ومكلف لو الخروج طول."],
         "now": [f"reserves ${nir.value / 1000:.1f}bn ({nir.date:%b %Y})", f"الاحتياطي {nir.value / 1000:.1f} مليار دولار"] if nir else None},
        {"icon": "🤝", "title": ["New inflows (IMF, Gulf, deals)", "دولارات جديدة (صندوق النقد والخليج والصفقات)"],
         "text": ["An IMF tranche, Gulf deposits or a big investment deal adds dollars and confidence quickly.",
                  "شريحة من صندوق النقد أو ودائع خليجية أو صفقة استثمار كبيرة بتزود الدولار والثقة بسرعة."], "now": None},
        {"icon": "🕊", "title": ["Calmer politics", "هدوء سياسي"],
         "text": ["If regional risk eases, hot money usually comes back as fast as it left — chasing Egypt's high yields.",
                  "لو المخاطر في المنطقة هديت، الأموال الساخنة غالبا بترجع بنفس سرعة ما خرجت، عشان العائد العالي في مصر."], "now": None},
    ]

    # impact outlook: what prices do if this persists, odds, tested accuracy, ranked reasons
    impact = None
    try:
        from .impact import build_impact
        impact = build_impact(v, move, move / max(days, 1) * 30)
    except Exception:  # noqa: BLE001
        impact = None
    reasons = []
    if impact:
        allc = next(c for c in impact["cats"] if c["id"] == "all")
        reasons.append(["Inflation already in the pipeline: prices rose at a pace worth " + f"{allc['pace']:.1f}% every 6 months over the past year — this momentum is most of the outlook.",
                        "تضخم موجود أصلا: الأسعار كانت بتزيد بسرعة تساوي " + f"{allc['pace']:.1f}% كل 6 شهور في آخر سنة، والسرعة دي هي أغلب التوقع."])
        big = sorted([c for c in impact["cats"] if c["id"] != "all" and c["test"].get("large")], key=lambda c: -c["test"]["large"]["extra_med"])  # history-based, valid even if a category series is not current
        if big:
            b0 = big[0]
            reasons.append([f"Dollar-priced imports: after past large dollar jumps, {b0['title'][0].lower()} rose the most — a median {b0['test']['large']['extra_med']:+.1f} points above its usual pace.",
                            f"الواردات اللي بتتسعر بالدولار: بعد قفزات الدولار الكبيرة اللي فاتت، {b0['title'][1]} زادت أكتر حاجة، بمتوسط {b0['test']['large']['extra_med']:+.1f} نقطة فوق سرعتها العادية."])
        reasons.append(["Administered prices move in steps: fuel (pricing committee) and medicine (drug authority) change only when officials decide, so part of the effect arrives later.",
                        "الأسعار المحددة إداريا بتتحرك على خطوات: الوقود (لجنة التسعير) والأدوية (هيئة الدواء) بيتغيروا لما المسؤولين يقرروا، فجزء من التأثير بيوصل متأخر."])
        gi2 = v.latest("fx_gold_implied")
        if gi2:
            g2 = _pct(gi2.value, now_v)
            reasons.append([f"Expectations: people rushing to dollars and gold would speed it up — today gold implies {g2:+.1f}% vs official, " + ("so no rush yet." if abs(g2) < 3 else "a sign of hedging."),
                            f"التوقعات: لو الناس جريت على الدولار والدهب الحركة هتسرع، والنهارده دولار الدهب {g2:+.1f}% عن الرسمي، " + ("يعني لسه مفيش جري." if abs(g2) < 3 else "وده علامة تحوط.")])
        if hm["headline"]:
            reasons.append([f"Hot money: foreign investors' net flows were {hm['headline'][0]} — if selling continues, the dollar keeps rising; if it stops, the pressure fades.",
                            f"الأموال الساخنة: صافي تعاملات الأجانب {hm['headline'][1]}، لو البيع استمر الدولار هيكمل، ولو وقف الضغط هيخف."])

    if direction == "up":
        title = [f"Why is the dollar rising? +{move:.1f}% in {days} days", f"ليه الدولار بيزيد؟ +{move:.1f}% في {days} يوم"]
    elif direction == "down":
        title = [f"Why is the dollar falling? {move:.1f}% in {days} days", f"ليه الدولار بينزل؟ {move:.1f}% في {days} يوم"]
    else:
        title = [f"The dollar is steady ({move:+.1f}% in {days} days)", f"الدولار ثابت ({move:+.1f}% في {days} يوم)"]
    lead_en = ", ".join(w["title"][0].lower() for w in main[:2]) or "no single clear driver"
    lead_ar = " و".join(w["title"][1] for w in main[:2]) or "مفيش سبب واحد واضح"
    summary = [f"From {_f(o0.value)} on {o0.date:%d %b} to {_f(now_v)} now (CBE). The data points mainly to: {lead_en}.",
               f"من {_f(o0.value)} يوم {o0.date:%d/%m} لـ {_f(now_v)} دلوقتي (البنك المركزي). والبيانات بتشاور أساسا على: {lead_ar}."]
    return {"direction": direction, "move_pct": round(move, 2), "days": days, "from": o0.value, "from_date": o0.date.isoformat(),
            "to": now_v, "to_date": now_date, "mid": mid["usd_egp"] if mid else None, "title": title, "summary": summary,
            "why": why, "if_continues": cont, "impact": impact, "reasons": reasons, "levers": levers if direction == "up" else levers[-1:],
            "sources": [cbe_src], "note": ["Signals consistent with the move — not proof of cause. The playbook is what usually happens, not a forecast.",
                                         "دي علامات متماشية مع الحركة، مش إثبات للسبب. والخطوات المتوقعة هي اللي بيحصل عادة، مش توقع أكيد."]}
