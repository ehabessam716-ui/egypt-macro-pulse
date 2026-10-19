"""The beginner 'chain': the economy as ~16 boxes connected by arrows, each with a live value, a status
(helping / hurting / steady for the pound) and plain-language tutor text (EN + Egyptian Arabic).

Statuses come from the same data and rules as the expert dashboard; nothing here invents numbers.
"""
from __future__ import annotations

from datetime import date

from ..data import DataView

HELP, HURT, STEADY, NODATA = -1, 1, 0, None


def _o(v: DataView, sid):
    o = v.latest(sid)
    return o if o is not None and o.stale < 2 else None


def _fmt(x, d=1):
    return f"{x:,.{d}f}"


def _src(o):
    return {"name": o.source_name, "url": o.source_url if o.source_url.startswith("http") else None, "date": o.date.isoformat()}


def build_chain(v: DataView, rules: dict) -> dict:
    R = rules
    fired = lambda rid: R.get(rid) is not None and R[rid].fired  # noqa: E731
    nodes = []

    def node(nid, row, en, ar, icon, value=None, value_ar=None, status=NODATA, now_en="", now_ar="", src=None,
             one=("", ""), why=("", ""), nxt=("", ""), series=None):
        nodes.append({"id": nid, "row": row, "title": [en, ar], "icon": icon, "value": [value, value_ar or value],
                      "status": status, "now": [now_en, now_ar], "one": list(one), "why": list(why), "next": list(nxt),
                      "sources": [s for s in (src or []) if s], "series": series or []})

    # ---------------- row 0: the world
    g = v.series("gpr_daily")
    gp = _o(v, "gpr_daily")
    status, now_en, now_ar = NODATA, "", ""
    if gp is not None and len(g) > 365:
        import numpy as np
        win = g[g.index > g.index[-1] - __import__("pandas").DateOffset(years=3)].rolling(7).mean().dropna()
        p90, avg = float(np.percentile(win, 90)), float(win.iloc[-1])
        status = HURT if avg > p90 else STEADY
        now_en = (f"The world's war-and-tension index is high ({avg:.0f}, above 90% of the last 3 years)." if avg > p90
                  else f"The world's war-and-tension index is {avg:.0f} — elevated but not extreme.")
        now_ar = ("مؤشر الحروب والتوترات في العالم عالي جدا." if avg > p90 else "مؤشر الحروب والتوترات في العالم مرتفع لكن مش في أعلى مستوياته.")
    node("wars", 0, "Wars & tensions", "الحروب والتوترات", "⚔", _fmt(avg, 0) if gp is not None and len(g) > 365 else None, None, status,
         now_en, now_ar, [_src(gp)] if gp else [],
         ("Conflicts in the region (Iran, Israel, Gaza, the Red Sea) shake everything else in this chain.",
          "النزاعات في المنطقة زي إيران وإسرائيل وغزة والبحر الأحمر بتهز كل حاجة تانية في السلسلة."),
         ("Wars push oil up, scare ships away from the Suez Canal, keep tourists home and make foreign investors nervous — four hits on Egypt's dollars at once.",
          "الحروب بتغلي البترول، وبتبعد السفن عن قناة السويس، وبتقلل السياح، وبتخوف المستثمرين الأجانب، يعني أربع ضربات للدولار في نفس الوقت."),
         ("If tensions ease, oil, Suez and tourism usually recover within months.", "لو التوترات هديت، البترول والقناة والسياحة غالبا بيتحسنوا خلال شهور."),
         ["gpr_daily", "gpr_egypt", "hormuz_ratio_7dma"])

    b = _o(v, "brent_fut") or _o(v, "brent")
    gap = _o(v, "brent_gap")
    bud = v.latest("budget_oil_assumption")
    st = NODATA
    if gap is not None:
        st = HURT if gap.value > 10 else (HELP if gap.value < -10 else STEADY)
    node("oil", 0, "Oil price", "سعر البترول", "⛽", f"${_fmt(b.value)}" if b else None, f"{_fmt(b.value)} دولار" if b else None, st,
         (f"Oil is ${b.value:.0f} a barrel — {'+' if gap.value >= 0 else '−'}${abs(gap.value):.0f} vs the ${bud.value:.0f} the government planned for." if b and gap and bud else ""),
         (f"البرميل بـ {b.value:.0f} دولار، يعني {gap.value:+.0f} دولار عن السعر اللي الحكومة حسبت عليه الموازنة." if b and gap and bud else ""),
         [_src(b)] if b else [],
         ("The world price of crude oil. Egypt now imports more fuel and gas than it exports.", "سعر البترول في العالم. مصر بقت بتستورد وقود وغاز أكتر ما بتصدر."),
         ("Every $10 more per barrel costs Egypt about 0.3% of its whole economy in extra dollars each year (IMF rule of thumb), and the government pays more fuel subsidy.",
          "كل 10 دولار زيادة في البرميل بتكلف مصر حوالي 0.3% من حجم الاقتصاد دولارات زيادة في السنة، والحكومة بتدفع دعم وقود أكتر."),
         ("Fuel prices are frozen until December — the increase is postponed, so petrol may rise in early 2027 if oil stays high.",
          "أسعار البنزين متثبتة لحد ديسمبر، يعني الزيادة متأجلة، وممكن البنزين يزيد أول 2027 لو البترول فضل غالي."),
         ["brent_fut", "brent_gap", "brent_spot_premium_pct"])

    d = _o(v, "dxy")
    ff = _o(v, "fed_funds")
    vx = _o(v, "vix")
    st = STEADY
    if vx is not None and vx.value > 25:
        st = HURT
    node("usd", 0, "US dollar & world mood", "الدولار الأمريكي ومزاج العالم", "🌐", f"VIX {vx.value:.0f}" if vx else None,
         f"مؤشر الخوف {vx.value:.0f}" if vx else None, st,
         (f"US interest rate {ff.value:.2f}%; global fear index (VIX) {vx.value:.0f} — " + ("investors are scared." if vx.value > 25 else "markets are calm.")) if ff and vx else "",
         (f"الفايدة الأمريكية {ff.value:.2f}% ومؤشر الخوف {vx.value:.0f}، " + ("المستثمرين خايفين." if vx.value > 25 else "والأسواق هادية.")) if ff and vx else "",
         [_src(x) for x in (ff, vx) if x],
         ("How attractive US savings are and how nervous world investors feel.", "الادخار في أمريكا جذاب قد إيه، والمستثمرين في العالم قلقانين قد إيه."),
         ("When US rates rise or markets panic, investors pull money out of countries like Egypt and park it in dollars.",
          "لما الفايدة الأمريكية تزيد أو الأسواق تخاف، المستثمرين بيسحبوا فلوسهم من بلاد زي مصر ويحطوها في الدولار."),
         ("Falling US rates usually help: money looks for higher returns in places like Egypt.", "لما الفايدة الأمريكية تقل الفلوس بتدور على عائد أعلى في بلاد زي مصر."),
         ["fed_funds", "us10y", "dxy", "vix"])

    # ---------------- row 1: dollars in
    rm = _o(v, "remittances")
    ry = _o(v, "remittances_yoy")
    st = NODATA if ry is None else (HELP if ry.value > 5 else HURT if ry.value < 0 else STEADY)
    node("remit", 1, "Money from Egyptians abroad", "تحويلات المصريين في الخارج", "✉",
         f"${_fmt(rm.value)}bn / month" if rm else None, f"{_fmt(rm.value)} مليار دولار في الشهر" if rm else None, st,
         (f"Egyptians abroad sent ${rm.value:.1f}bn in {rm.date:%B %Y}, {ry.value:+.0f}% vs a year earlier." if rm and ry else ""),
         (f"المصريين في الخارج بعتوا {rm.value:.1f} مليار دولار في شهر {rm.date.month}/{rm.date.year}، بزيادة {ry.value:+.0f}% عن السنة اللي فاتت." if rm and ry else ""),
         [_src(rm)] if rm else [],
         ("Salaries that Egyptians working in the Gulf and elsewhere send home — the biggest single source of dollars.",
          "المرتبات اللي المصريين اللي شغالين في الخليج وغيره بيبعتوها لأهاليهم، وده أكبر مصدر للدولار."),
         ("More dollars arriving through banks means the pound is easier to defend.", "دولارات أكتر داخلة البنوك يعني الجنيه أسهل يتسند."),
         ("If the Gulf economies slow, or people trust the black market more than banks, this flow shrinks.",
          "لو اقتصاد الخليج ضعف أو الناس وثقت في السوق السودا أكتر من البنوك، التحويلات بتقل."),
         ["remittances", "remittances_yoy", "remittances_12m_sum"])

    tr = v.series("tourism_receipts_fy")
    st = NODATA
    tnow_en = tnow_ar = ""
    to = _o(v, "tourism_receipts_fy")
    if len(tr) >= 2:
        ch = (tr.iloc[-1] / tr.iloc[-2] - 1) * 100
        st = HELP if ch > 5 else HURT if ch < 0 else STEADY
        tnow_en = f"Tourism brought ${tr.iloc[-1]:.1f}bn last fiscal year ({ch:+.0f}% vs the year before)."
        tnow_ar = f"السياحة دخلت {tr.iloc[-1]:.1f} مليار دولار في السنة المالية اللي فاتت ({ch:+.0f}% عن اللي قبلها)."
    node("tourism", 1, "Tourism", "السياحة", "✈", f"${_fmt(tr.iloc[-1])}bn / year" if len(tr) else None,
         f"{_fmt(tr.iloc[-1])} مليار دولار في السنة" if len(tr) else None, st, tnow_en, tnow_ar, [_src(to)] if to else [],
         ("Dollars spent by visitors to Egypt.", "الدولارات اللي السياح بيصرفوها في مصر."),
         ("Tourists pay in foreign currency, adding to Egypt's dollar supply.", "السياح بيدفعوا بالعملة الأجنبية، فبيزودوا الدولارات في مصر."),
         ("Wars in the region are the biggest risk; calm and good flight links help it grow.", "الحروب في المنطقة أكبر خطر عليها، والهدوء والطيران الكويس بيساعدوها تكبر."),
         ["tourism_receipts_fy", "tourism_arrivals_ytd"])

    sz = _o(v, "suez_ratio_7dma")
    st = NODATA if sz is None else (HURT if sz.value < 0.6 else HELP if sz.value > 0.85 else STEADY)
    node("suez", 1, "Suez Canal", "قناة السويس", "⚓", f"{sz.value * 100:.0f}% of normal" if sz else None,
         f"{sz.value * 100:.0f}% من الطبيعي" if sz else None, st,
         (f"Ships through the canal are at {sz.value * 100:.0f}% of their 2023 level." if sz else ""),
         (f"عدد السفن في القناة {sz.value * 100:.0f}% من مستوى سنة 2023." if sz else ""), [_src(sz)] if sz else [],
         ("Fees ships pay to cross the canal — paid in dollars.", "رسوم المرور اللي السفن بتدفعها بالدولار."),
         ("Fewer ships = fewer dollars. Attacks in the Red Sea made many ships sail around Africa instead.",
          "سفن أقل يعني دولارات أقل، والهجمات في البحر الأحمر خلت سفن كتير تلف حوالين أفريقيا."),
         ("Traffic comes back only when the Red Sea is safe again.", "الحركة مش هترجع غير لما البحر الأحمر يبقى آمن."),
         ["suez_ratio_7dma", "suez_transits", "suez_receipts_fy"])

    from ..fxstory import hot_money
    H = hot_money(v)
    cp = _o(v, "cib_gdr_premium_pct")
    st = NODATA if not H["facts_en"] else (HURT if H["status"] == 1 else HELP if H["status"] == -1 else STEADY)
    hv_en, hv_ar = H["headline"] or ((f"{cp.value:+.1f}% CIB gap", f"فرق {cp.value:+.1f}%") if cp else (None, None))
    node("hot", 1, "Foreign investors (hot money)", "المستثمرين الأجانب (الأموال الساخنة)", "⇅",
         hv_en, hv_ar, st,
         ("; ".join(H["facts_en"]).capitalize() + "." if H["facts_en"] else ""), ("، و".join(H["facts_ar"]) + "." if H["facts_ar"] else ""),
         H["sources"],
         ("Foreigners who buy Egyptian government bills and shares for the high interest — fast money that can leave just as fast.",
          "أجانب بيشتروا أذون خزانة وأسهم مصرية عشان الفايدة العالية، فلوس بتدخل بسرعة وممكن تخرج بنفس السرعة."),
         ("When they come, they bring dollars and the pound strengthens; when they rush out, the pound comes under heavy pressure (as in 2022).",
          "لما بيدخلوا بيجيبوا دولارات والجنيه بيقوى، ولما بيخرجوا مرة واحدة الجنيه بيتضغط جامد زي اللي حصل في 2022."),
         ("They stay while Egypt's interest rate stays well above inflation and the pound looks stable.", "بيفضلوا طول ما الفايدة في مصر أعلى بكتير من التضخم والجنيه شكله مستقر."),
         ["egx_foreign_net", "egx30_usd", "cib_gdr_premium_pct", "tbill_3m_btc", "carry_ex_post_3m"])

    fd = R.get("FD03")
    st = NODATA if fd is None or not fd.evaluable else (int(fd.direction) if fd.fired else STEADY)
    node("imf", 1, "IMF & Gulf support", "دعم صندوق النقد والخليج", "🤝", "Programme ends Dec 2026", "البرنامج بيخلص ديسمبر 2026", st,
         (fd.vals.get("detail", "") if fd else ""), (fd.vals.get("detail_ar", "") if fd else ""), [],
         ("Loans from the IMF and deposits or big investments from Gulf countries.", "قروض صندوق النقد وودائع أو استثمارات كبيرة من دول الخليج."),
         ("They add dollars and, just as important, give other investors confidence.", "بيدخلوا دولارات، والأهم إنهم بيدوا ثقة لباقي المستثمرين."),
         ("The current IMF programme ends in December 2026 — what replaces it matters.", "برنامج صندوق النقد الحالي بيخلص في ديسمبر 2026، واللي هييجي بعده مهم."),
         ["imf_weo_gdp"])

    # ---------------- row 1b: dollars out
    io = v.series("imports_oil_fy")
    st = NODATA
    en_now = ar_now = ""
    if len(io) >= 2:
        ch = (io.iloc[-1] / io.iloc[-2] - 1) * 100
        st = HURT if ch > 10 or (gap is not None and gap.value > 10) else STEADY
        en_now = f"Egypt spent ${io.iloc[-1]:.1f}bn on oil & gas imports last fiscal year ({ch:+.0f}%)."
        ar_now = f"مصر صرفت {io.iloc[-1]:.1f} مليار دولار على استيراد البترول والغاز في السنة المالية اللي فاتت ({ch:+.0f}%)."
    node("energy", 2, "Fuel & gas imports", "استيراد البترول والغاز", "🛢", f"${_fmt(io.iloc[-1])}bn / year" if len(io) else None,
         f"{_fmt(io.iloc[-1])} مليار دولار في السنة" if len(io) else None, st, en_now, ar_now, [],
         ("Dollars paid abroad for petrol, diesel and liquefied gas.", "الدولارات اللي بتتدفع برة عشان البنزين والسولار والغاز المسال."),
         ("Higher oil prices or more gas imports in summer mean more dollars leaving Egypt.", "البترول الغالي أو استيراد غاز أكتر في الصيف يعني دولارات أكتر خارجة من مصر."),
         ("Watch oil prices and summer power demand.", "خلي عينك على سعر البترول والكهربا في الصيف."),
         ["imports_oil_fy", "lng_imports", "ttf_fut"])

    wh = v.series("wheat")
    st = NODATA
    en_now = ar_now = ""
    if len(wh) > 64:
        ch = (wh.iloc[-1] / wh.iloc[-64] - 1) * 100
        st = HURT if ch > 20 else HELP if ch < -15 else STEADY
        en_now = f"World wheat price {ch:+.0f}% over 3 months."
        ar_now = f"سعر القمح العالمي {ch:+.0f}% في 3 شهور."
    node("food", 2, "Food imports (wheat)", "استيراد الأكل (القمح)", "🌾", f"{wh.iloc[-1]:.0f}¢" if len(wh) else None, None, st,
         en_now, ar_now, [_src(v.latest("wheat"))] if v.latest("wheat") else [],
         ("Egypt is one of the world's biggest wheat buyers — bread is subsidized.", "مصر من أكبر مشتري القمح في العالم، والعيش مدعم."),
         ("Pricier wheat means more dollars out and a bigger subsidy bill.", "القمح الغالي يعني دولارات أكتر خارجة ودعم أكبر."),
         ("Harvests and Black Sea exports drive the price.", "المحاصيل وصادرات البحر الأسود هي اللي بتحدد السعر."),
         ["wheat", "wheat_monthly"])

    ds = _o(v, "debt_service_next_year_to_nir")
    st = NODATA if ds is None else (HURT if ds.value > 50 else STEADY)
    node("debt", 2, "Debt payments", "سداد الديون", "🏦", f"{ds.value:.0f}% of savings" if ds else None,
         f"{ds.value:.0f}% من الاحتياطي" if ds else None, st,
         (f"Next year's scheduled foreign-debt payments equal {ds.value:.0f}% of the central bank's dollar savings." if ds else ""),
         (f"أقساط الديون الخارجية السنة الجاية تساوي {ds.value:.0f}% من مدخرات البنك المركزي بالدولار." if ds else ""),
         [_src(ds)] if ds else [],
         ("Loans Egypt must repay to foreign lenders, with interest.", "القروض اللي مصر لازم ترجعها للمقرضين الأجانب بفوايدها."),
         ("Every repayment is dollars leaving the country.", "كل قسط معناه دولارات خارجة من البلد."),
         ("Big repayment years need new loans, investment or savings to cover them.", "سنين السداد الكبيرة محتاجة قروض جديدة أو استثمار أو صرف من الاحتياطي."),
         ["debt_service_next_year_to_nir", "ext_debt_stock"])

    # ---------------- row 3: savings + pound
    nir = _o(v, "nir")
    mi = _o(v, "nir_months_imports")
    ch3 = _o(v, "nir_chg_3m")
    st = NODATA if nir is None else (HELP if (ch3 and ch3.value > 0) else HURT if (ch3 and ch3.value < -1000) else STEADY)
    node("reserves", 3, "Egypt's dollar savings", "مدخرات مصر بالدولار", "🏛", f"${nir.value / 1000:.1f}bn" if nir else None,
         f"{nir.value / 1000:.1f} مليار دولار" if nir else None, st,
         (f"The central bank holds ${nir.value / 1000:.1f}bn — enough for about {mi.value:.1f} months of imports." if nir and mi else ""),
         (f"البنك المركزي معاه {nir.value / 1000:.1f} مليار دولار، تكفي استيراد حوالي {mi.value:.1f} شهور." if nir and mi else ""),
         [_src(nir)] if nir else [],
         ("Dollars and gold kept by the Central Bank for emergencies (net international reserves).", "الدولارات والدهب اللي البنك المركزي شايلهم للطوارئ."),
         ("A big cushion lets Egypt pay for imports and debts even when inflows dip, which calms the pound.",
          "السند الكبير بيخلي مصر تقدر تدفع الاستيراد والديون حتى لو الدولارات الداخلة قلت، وده بيطمن الجنيه."),
         ("Falling savings while the pound stays fixed is a warning sign that the rate is being defended.",
          "لو المدخرات بتقل والجنيه ثابت، دي علامة إن السعر بيتسند."),
         ["nir", "nir_months_imports", "nir_chg_3m"])

    fx = _o(v, "fx_cbe_official")
    f20 = _o(v, "fx_chg_20d")
    gg = _o(v, "gold_gap_pct")
    st = NODATA if f20 is None else (HURT if f20.value > 1 else HELP if f20.value < -1 else STEADY)
    node("pound", 3, "The pound", "الجنيه", "£", f"{fx.value:.2f} per $" if fx else None, f"{fx.value:.2f} جنيه للدولار" if fx else None, st,
         (f"1 US dollar costs {fx.value:.2f} pounds ({f20.value:+.1f}% in a month). Gold prices imply {gg.value:+.1f}% vs official — "
          + ("normal." if abs(gg.value) < 3 else "a warning sign.") if fx and f20 and gg else ""),
         (f"الدولار بـ {fx.value:.2f} جنيه ({f20.value:+.1f}% في شهر). ودولار الدهب بفرق {gg.value:+.1f}% عن الرسمي، "
          + ("وده عادي." if abs(gg.value) < 3 else "ودي علامة تحذير.") if fx and f20 and gg else ""),
         [_src(fx)] if fx else [],
         ("How many Egyptian pounds you need to buy one US dollar.", "محتاج كام جنيه عشان تشتري دولار واحد."),
         ("It moves with the balance of everything above: dollars coming in vs dollars going out, backed by the savings.",
          "بيتحرك حسب كل اللي فوق: الدولارات الداخلة مقابل الخارجة، والمدخرات بتسنده."),
         ("A weaker pound makes imported goods — fuel, food, medicines — more expensive within months.",
          "الجنيه الأضعف بيغلي المستورد زي الوقود والأكل والأدوية خلال شهور."),
         ["fx_cbe_official", "fx_gold_implied", "gold_gap_pct", "fx_chg_20d"])

    # ---------------- row 4: prices & rates
    cpi = _o(v, "cpi_urban_yoy")
    cs = v.series("cpi_urban_yoy")
    st = NODATA if cpi is None else (HURT if len(cs) > 1 and cs.iloc[-1] > cs.iloc[-2] else HELP if len(cs) > 1 and cs.iloc[-1] < cs.iloc[-2] else STEADY)
    node("prices", 4, "Prices (inflation)", "الأسعار (التضخم)", "🛒", f"{cpi.value:.1f}% a year" if cpi else None,
         f"{cpi.value:.1f}% في السنة" if cpi else None, st,
         (f"Prices in cities are {cpi.value:.1f}% higher than a year ago" + (f" (last month {cs.iloc[-2]:.1f}%)." if len(cs) > 1 else ".") if cpi else ""),
         (f"الأسعار في المدن أعلى {cpi.value:.1f}% من السنة اللي فاتت" + (f" (الشهر اللي قبله {cs.iloc[-2]:.1f}%)." if len(cs) > 1 else ".") if cpi else ""),
         [_src(cpi)] if cpi else [],
         ("How fast the cost of living is rising.", "تكلفة المعيشة بتزيد بسرعة قد إيه."),
         ("A weaker pound, pricier fuel or food push prices up; the central bank answers with higher interest rates.",
          "ضعف الجنيه وغلو البنزين أو الأكل بيرفعوا الأسعار، والبنك المركزي بيرد بفايدة أعلى."),
         ("Frozen fuel prices and earlier pound moves mean some increases are still on their way.", "تثبيت البنزين وحركة الجنيه اللي فاتت معناهم إن فيه زيادات لسه جاية."),
         ["cpi_urban_yoy", "cpi_core_yoy", "cpi_urban_mom"])

    odr = v.latest("cbe_odr")
    rr = _o(v, "real_headline")
    st = NODATA if rr is None else (HELP if rr.value > 5 else HURT if rr.value < 2 else STEADY)
    node("rates", 4, "Interest rates", "الفايدة", "%", f"{odr.value:.2f}%" if odr else None, None, st,
         (f"The central bank pays {odr.value:.2f}% on deposits — {rr.value:+.1f} points above inflation." if odr and rr else ""),
         (f"البنك المركزي بيدي {odr.value:.2f}% على الإيداع، يعني {rr.value:+.1f} نقطة فوق التضخم." if odr and rr else ""),
         [_src(odr)] if odr else [],
         ("The interest rate set by the Central Bank of Egypt, about 8 times a year.", "الفايدة اللي البنك المركزي بيحددها حوالي 8 مرات في السنة."),
         ("High rates fight inflation and attract foreign money (helping the pound), but make loans expensive and slow businesses.",
          "الفايدة العالية بتحارب التضخم وبتجذب الفلوس الأجنبية وده بيساعد الجنيه، بس بتغلي القروض وبتبطأ الشركات."),
         ("Next decision: see the calendar. Cuts become likely when inflation clearly falls.", "القرار الجاي في الأجندة، والتخفيض بيبقى وارد لما التضخم يقل بوضوح."),
         ["cbe_odr", "real_headline", "tbill_12m_yield"])

    # ---------------- row 5: your life
    fuel = v.latest("fuel_92")
    eda = _o(v, "eda_signal")
    node("life", 5, "Your daily life", "حياتك اليومية", "🏠", f"Petrol 92: {fuel.value:.2f} EGP" if fuel else None,
         f"بنزين 92: {fuel.value:.2f} جنيه" if fuel else None, STEADY,
         ("Petrol, bread, medicines and rent all respond to this chain — with a delay of weeks to months." +
          (f" Drug-repricing signal: {eda.value:+.1f}% (companies can ask for increases at +10%)." if eda else "")),
         ("البنزين والعيش والأدوية والإيجار كلهم بيتأثروا بالسلسلة دي بعد أسابيع أو شهور." +
          (f" مؤشر إعادة تسعير الدوا: {eda.value:+.1f}% والشركات تقدر تطلب زيادة عند 10%." if eda else "")),
         [_src(fuel)] if fuel else [],
         ("Where the whole chain ends up: what you pay.", "آخر السلسلة: اللي انت بتدفعه."),
         ("A weaker pound and higher oil prices reach shop prices, fuel and medicines after a few months.", "ضعف الجنيه وغلو البترول بيوصلوا لأسعار المحلات والبنزين والأدوية بعد كام شهر."),
         ("Watch the fuel-price committee in January 2027 and the next inflation numbers.", "خلي عينك على لجنة تسعير الوقود في يناير 2027 وأرقام التضخم الجاية."),
         ["fuel_92", "cpi_health_yoy", "eda_signal"])

    edges = [
        ("wars", "oil", "pushes up", "بتغلي"), ("wars", "suez", "scares ships away", "بتبعد السفن"),
        ("wars", "tourism", "keeps visitors away", "بتبعد السياح"), ("wars", "hot", "scares investors", "بتخوف المستثمرين"),
        ("oil", "energy", "makes more expensive", "بتغلي"), ("usd", "hot", "pulls money to the US", "بتسحب الفلوس لأمريكا"),
        ("remit", "reserves", "brings dollars in", "بتدخل دولارات"), ("tourism", "reserves", "brings dollars in", "بتدخل دولارات"),
        ("suez", "reserves", "brings dollars in", "بتدخل دولارات"), ("hot", "pound", "brings — or pulls — dollars", "بتدخل أو بتسحب دولارات"),
        ("imf", "reserves", "adds dollars & confidence", "بتزود الدولارات والثقة"), ("energy", "pound", "takes dollars out", "بتخرج دولارات"),
        ("food", "pound", "takes dollars out", "بتخرج دولارات"), ("debt", "reserves", "takes dollars out", "بتخرج دولارات"),
        ("reserves", "pound", "protects", "بتحمي"), ("pound", "prices", "weaker pound = higher prices", "جنيه أضعف يعني أسعار أعلى"),
        ("prices", "rates", "CBE raises rates to fight it", "المركزي بيرفع الفايدة"), ("rates", "hot", "high rates attract", "الفايدة العالية بتجذب"),
        ("prices", "life", "what you pay", "اللي بتدفعه"), ("oil", "life", "petrol prices later", "البنزين بعدين"),
    ]
    rows = [
        {"id": 0, "title": ["The world", "العالم"]},
        {"id": 1, "title": ["Dollars coming in", "الدولارات الداخلة"]},
        {"id": 2, "title": ["Dollars going out", "الدولارات الخارجة"]},
        {"id": 3, "title": ["Savings & the pound", "المدخرات والجنيه"]},
        {"id": 4, "title": ["Prices & interest", "الأسعار والفايدة"]},
        {"id": 5, "title": ["You", "انت"]},
    ]
    tour = ["wars", "oil", "remit", "suez", "hot", "energy", "reserves", "pound", "prices", "rates", "life"]
    return {"nodes": nodes, "edges": [{"from": a, "to": b, "label": [e, r]} for a, b, e, r in edges], "rows": rows, "tour": tour}


HURT_WHY = {"oil": ("expensive oil", "غلو البترول"), "suez": ("fewer ships through Suez", "قلة السفن في قناة السويس"),
            "wars": ("regional tensions", "التوترات في المنطقة"), "pound": ("a weakening pound", "ضعف الجنيه"),
            "hot": ("foreign money leaving", "خروج الأموال الأجنبية"), "energy": ("a bigger fuel import bill", "فاتورة استيراد الوقود"),
            "imf": ("the IMF programme ending soon", "قرب نهاية برنامج صندوق النقد"), "prices": ("rising prices", "زيادة الأسعار"),
            "rates": ("low real interest rates", "ضعف الفايدة الحقيقية"), "food": ("pricier wheat", "غلو القمح"),
            "debt": ("heavy debt payments", "أقساط الديون"), "remit": ("weaker remittances", "ضعف التحويلات"),
            "tourism": ("weaker tourism", "ضعف السياحة"), "usd": ("global risk-off", "خوف الأسواق العالمية"),
            "reserves": ("falling reserves", "نزول الاحتياطي")}
HELP_WHY = {"remit": ("strong money transfers from Egyptians abroad", "تحويلات المصريين القوية"),
            "tourism": ("growing tourism", "نمو السياحة"), "reserves": ("record dollar savings", "الاحتياطي القياسي"),
            "prices": ("easing inflation", "هدوء التضخم"), "rates": ("high real interest rates", "الفايدة الحقيقية العالية"),
            "suez": ("Suez traffic recovering", "رجوع حركة القناة"), "oil": ("cheap oil", "رخص البترول"),
            "hot": ("foreign money coming in", "دخول أموال أجنبية"), "pound": ("a firmer pound", "ثبات الجنيه"),
            "imf": ("IMF and Gulf support", "دعم صندوق النقد والخليج"), "food": ("cheaper wheat", "رخص القمح")}
# which boxes matter most for the pound when several are red
PRIORITY = ["oil", "hot", "pound", "suez", "energy", "wars", "reserves", "imf", "prices", "remit", "tourism", "rates", "food", "debt", "usd"]


def headline(chain: dict, ppi: dict) -> dict:
    """One plain sentence for the top of the page."""
    v = ppi.get("value")
    order = {k: i for i, k in enumerate(PRIORITY)}
    hurt = sorted([n for n in chain["nodes"] if n["status"] == HURT and n["id"] in HURT_WHY and n["id"] != "pound"], key=lambda n: order.get(n["id"], 99))
    helping = sorted([n for n in chain["nodes"] if n["status"] == HELP and n["id"] in HELP_WHY], key=lambda n: order.get(n["id"], 99))
    if v is None:
        return {"en": "We don't have enough fresh data to judge the pound today.", "ar": "مفيش بيانات حديثة كفاية نحكم بيها على الجنيه النهارده.",
                "good_en": "", "good_ar": "", "ppi": v}
    if v > 40:
        en, ar = "The pound is under strong pressure today", "الجنيه تحت ضغط قوي النهارده"
    elif v > 10:
        en, ar = "The pound is under mild pressure today", "الجنيه تحت ضغط خفيف النهارده"
    elif v < -40:
        en, ar = "Conditions strongly support the pound today", "الظروف بتسند الجنيه جامد النهارده"
    elif v < -10:
        en, ar = "Conditions support the pound today", "الظروف بتسند الجنيه النهارده"
    else:
        en, ar = "The pound is broadly stable today", "الجنيه مستقر تقريبا النهارده"
    if hurt and v > -10:
        en += " — mainly because of " + " and ".join(HURT_WHY[n["id"]][0] for n in hurt[:2]) + "."
        ar += "، والسبب الأساسي " + " و".join(HURT_WHY[n["id"]][1] for n in hurt[:2]) + "."
    else:
        en += "."
        ar += "."
    good_en = ("Helping it: " + ", ".join(HELP_WHY[n["id"]][0] for n in helping[:3]) + ".") if helping else ""
    good_ar = ("واللي بيسنده: " + "، ".join(HELP_WHY[n["id"]][1] for n in helping[:3]) + ".") if helping else ""
    return {"en": en, "ar": ar, "good_en": good_en, "good_ar": good_ar, "ppi": v}
