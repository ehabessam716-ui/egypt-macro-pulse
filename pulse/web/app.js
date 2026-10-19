/* Pulse · نبض — Egypt Macro Pulse web app.
   Vanilla JS, no build step. Data arrives as JS files (works from file:// and from `pulse serve`). */
(() => {
  'use strict';

  // ------------------------------------------------------------------ i18n
  const I18N = {
    tagline: ['Egypt Macro · what moves the pound', 'الاقتصاد المصري · إيه اللي بيحرك الجنيه'],
    search: ['Search', 'بحث'], update_now: ['Update now', 'حدّث دلوقتي'], to_move: ['to move', 'للتنقل'], to_open: ['to open', 'للفتح'],
    overview: ['Overview', 'الصورة الكاملة'], signals: ['Signals', 'الإشارات'], calendar: ['Calendar', 'الأجندة'],
    brief: ['Daily brief', 'الموجز اليومي'], data: ['Data & sources', 'البيانات والمصادر'], more: ['More', 'المزيد'],
    ppi: ['Pound Pressure Index', 'مؤشر الضغط على الجنيه'], ppi_scale: ['−100 relief · +100 pressure', 'سالب 100 راحة · موجب 100 ضغط'],
    coverage: ['coverage', 'التغطية'], insufficient: ['Not enough fresh data — shown for reference only', 'البيانات مش كفاية — الرقم للاسترشاد بس'],
    strong_relief: ['Strong relief', 'راحة قوية للجنيه'], relief: ['Relief', 'راحة للجنيه'], balanced: ['Balanced', 'متوازن'],
    pressure: ['Pressure', 'ضغط على الجنيه'], strong_pressure: ['Strong pressure', 'ضغط قوي على الجنيه'],
    todays_story: ["Today's story", 'حكاية النهارده'], see_all: ['See all signals', 'كل الإشارات'],
    key_numbers: ['Key numbers', 'أهم الأرقام'], upcoming: ['Coming up', 'اللي جاي'], active_events: ['Active events', 'الأحداث الشغالة'],
    no_data: ['No data', 'مفيش بيانات'], manual_hint: ['Manual input — add it in manual_inputs.xlsx', 'إدخال يدوي — ضيفه في ملف الإدخال اليدوي'],
    auto_hint: ['Not published yet or source unreachable', 'لسه مانزلش أو المصدر مش متاح'],
    vs: ['vs', 'مقارنة بـ'], source: ['Source', 'المصدر'], observed: ['Observed', 'تاريخ الرقم'], released: ['Released', 'تاريخ النشر'],
    quality: ['Quality', 'الجودة'], frequency: ['Frequency', 'التكرار'], definition: ['Definition', 'التعريف'], unit: ['Unit', 'الوحدة'],
    stale: ['stale', 'قديم'], very_stale: ['very stale — excluded', 'قديم جدا — مستبعد'], closed: ['market closed', 'سوق مقفول'],
    conflict: ['sources disagree', 'المصادر مختلفة'], download_csv: ['Download CSV', 'تحميل الجدول'], history: ['History', 'التاريخ'],
    latest_obs: ['Latest observations', 'آخر القراءات'], fired: ['Fired', 'اشتغلت'], all: ['All', 'الكل'],
    not_evaluable: ['Not evaluable', 'مش ممكن نقيمها'], notes: ['Notes', 'ملاحظات'], learn: ['Learn the concept', 'افهم الفكرة'],
    inputs: ['Inputs (source, date)', 'المدخلات (المصدر والتاريخ)'], missing: ['Missing inputs', 'بيانات ناقصة'],
    strength: ['strength', 'القوة'], tool_default: ['thresholds are tool defaults', 'الحدود افتراضية من الأداة'],
    review_queue: ['Review queue', 'أحداث مستنية مراجعة'], review_hint: ['Proposed from headlines. Counted only after 2 independent outlets report it within 48 h, or you confirm it.', 'مقترحة من العناوين، ومش بتدخل في الحسابات غير لما مصدرين مستقلين ينشروها في خلال 48 ساعة أو تأكدها انت.'],
    weight_left: ['weight left', 'الأثر الباقي'], tag_only: ['tag only', 'للعلم بس'],
    updated: ['updated', 'اتحدث'], live: ['Live', 'مباشر'], snapshot: ['Snapshot', 'نسخة ثابتة'], next_update: ['next update', 'التحديث الجاي'],
    ago_now: ['just now', 'دلوقتي'], ago_min: ['min ago', 'دقيقة'], ago_h: ['h ago', 'ساعة'], ago_d: ['d ago', 'يوم'],
    in_: ['in', 'بعد'], today: ['Today', 'النهارده'], tomorrow: ['Tomorrow', 'بكره'],
    new_data: ['New data', 'بيانات جديدة'], changed: ['indicators changed', 'مؤشرات اتغيرت'], running: ['Updating…', 'بنحدّث…'],
    run_started: ['Update started — new numbers appear here automatically.', 'التحديث بدأ — الأرقام الجديدة هتظهر هنا لوحدها.'],
    run_done: ['Update finished', 'التحديث خلص'], run_failed: ['Update failed — see logs/pulse.log', 'التحديث فشل — شوف ملف السجل'],
    coverage_title: ['Data coverage', 'تغطية البيانات'], fresh: ['fresh', 'حديث'], with_data: ['with data', 'فيها بيانات'],
    sources_title: ['Collectors — last run', 'المصادر — آخر تشغيل'], all_series: ['All indicators', 'كل المؤشرات'],
    filter_series: ['Filter indicators…', 'دوّر في المؤشرات…'], ppi_history: ['Pound Pressure Index over time', 'مؤشر الضغط على الجنيه عبر الوقت'],
    backtest_note: ['Weekly point-in-time backtest (learning only, no predictive claim) plus live daily values.', 'اختبار أسبوعي بالبيانات المتاحة وقتها (للتعلم بس) مع القيم اليومية.'],
    disclaimer: ['Learning tool, not financial advice. Every number shows its source and date; missing values stay "no data" — nothing is estimated. Thresholds and weights are tool defaults.',
      'أداة تعليمية مش نصيحة استثمارية. كل رقم معاه مصدره وتاريخه، والناقص بيفضل مكتوب مفيش بيانات من غير تقدير.'],
    inflation_idx: ['Inflation pressure', 'ضغط التضخم'], growth_idx: ['Growth', 'النمو'],
    chart_fx: ['USD/EGP — official vs gold-implied vs market', 'الدولار — الرسمي ودولار الدهب والسوق'],
    chart_real: ['Real policy rate (deposit rate − inflation)', 'الفايدة الحقيقية (الإيداع ناقص التضخم)'],
    chart_nir: ['Net international reserves (USD bn)', 'صافي الاحتياطيات الدولية (مليار دولار)'],
    chart_brent: ['Brent vs the budget assumption', 'البترول مقارنة بسعر الموازنة'],
    chart_choke: ['Shipping chokepoints vs 2023 (7-day avg)', 'حركة السفن مقارنة بسنة 2023'],
    chart_remit: ['Remittances, monthly (USD bn)', 'تحويلات المصريين بالخارج شهريا (مليار دولار)'],
    chart_gpr: ['Geopolitical risk (daily)', 'المخاطر الجيوسياسية (يومي)'], chart_pmi: ['Egypt PMI (50 = no change)', 'مؤشر مديري المشتريات (50 = ثبات)'],
    chart_cpi: ['Inflation vs the policy rate', 'التضخم مقابل الفايدة'],
    official: ['CBE official (buy)', 'الرسمي (شراء)'], gold_implied: ['Gold-implied', 'دولار الدهب'], market: ['Market (Yahoo)', 'السوق (ياهو)'],
    budget: ['Budget', 'الموازنة'], spot: ['Spot (FRED/EIA)', 'الفوري'], futures: ['Futures (Yahoo)', 'الآجل'],
    vs_urban: ['vs urban CPI', 'مقابل التضخم العام'], vs_core: ['vs core CPI', 'مقابل التضخم الأساسي'], vs_cbe: ['vs CBE forecast', 'مقابل توقع المركزي'],
    urban_cpi: ['Urban CPI y/y', 'التضخم العام'], core_cpi: ['Core CPI y/y', 'التضخم الأساسي'], deposit_rate: ['Deposit rate', 'فايدة الإيداع'],
    baseline: ['2023 average', 'متوسط 2023'], weak: ['weak (0.6)', 'ضعيف'], daily: ['daily', 'يومي'], avg7: ['7-day average', 'متوسط 7 أيام'],
    pressure_word: ['pressure', 'ضغط'], relief_word: ['relief', 'راحة'], note_word: ['note', 'ملاحظة'],
    print: ['Print', 'اطبع'], open_file: ['Open file', 'افتح الملف'], domain_signals: ['Signals in this area', 'إشارات القسم ده'],
    nothing_fired: ['Nothing fired here today.', 'مفيش إشارات هنا النهارده.'], events_title: ['Events', 'الأحداث'],
    pending: ['pending', 'مستني'], status: ['status', 'الحالة'], rows: ['rows', 'صفوف'], error: ['error', 'خطأ'],
    queue_empty: ['Queue empty.', 'مفيش أحداث مستنية.'], no_events: ['No active events.', 'مفيش أحداث شغالة.'],
    explain: ['Explain', 'اشرح'], what_means: ['What this means', 'يعني إيه الرقم ده'], what_is: ['What it is', 'هو إيه'],
    what_moves: ['What usually moves it', 'إيه اللي بيحركه'], what_happened: ['What happened', 'إيه اللي حصل'],
    may_lead: ['What it may lead to', 'ممكن يؤدي لإيه'], alongside: ['Moved alongside it (same period)', 'اتحرك معاه في نفس الفترة'],
    signals_using: ['Signals that use this number today', 'إشارات النهارده اللي بتستخدم الرقم ده'], related_events: ['Related events', 'أحداث مرتبطة'],
    not_proof: ['Possible reasons from the data — not proven causes.', 'أسباب محتملة من البيانات، مش إثبات.'],
    rose: ['rose', 'زاد'], fell: ['fell', 'قل'], flat: ['was unchanged', 'فضل ثابت'], from_: ['from', 'من'], to_: ['to', 'لـ'],
    if_rises: ['If it rises', 'لو زاد'], if_falls: ['If it falls', 'لو قل'],
    no_history: ['Only one reading so far — history builds from now.', 'فيه قراءة واحدة بس لحد دلوقتي، والتاريخ هيتبني من النهارده.'],
    right_now: ['Right now', 'دلوقتي'], live_note: ['Delayed market quotes, refreshed automatically about every 15 minutes. Official figures update when the source publishes.',
      'أسعار السوق متأخرة شوية وبتتحدث لوحدها كل ربع ساعة تقريبا، والأرقام الرسمية بتتحدث لما المصدر ينشر.'],
    live_reads: ['Live reads', 'قراءة سريعة'], headlines: ['Latest headlines', 'آخر الأخبار'], closed_mkt: ['closed', 'مقفول'],
    open_mkt: ['live', 'شغال'], cbe_today: ['CBE official rate', 'السعر الرسمي للبنك المركزي'], gold21_now: ['Gold 21K in Egypt', 'جرام الدهب عيار 21'],
    prices_updated: ['prices updated', 'الأسعار اتحدثت'],
    simple: ['Simple', 'بسيط'], pro: ['Pro', 'محترف'], home: ['Today', 'النهارده'], learn_tab: ['Learn', 'اتعلم'], live_tab: ['Live', 'مباشر'],
    chain_title: ['How it all connects', 'إزاي كل حاجة مرتبطة ببعض'],
    chain_hint: ['Tap any box to learn what it is and why it matters. Red = hurting the pound · Blue = helping · Grey = steady.',
      'دوس على أي مربع تعرف هو إيه وليه مهم. الأحمر بيضغط على الجنيه، والأزرق بيساعده، والرمادي ثابت.'],
    start_tour: ['Start the 2-minute tour', 'ابدأ جولة الدقيقتين'], helping: ['helping the pound', 'بيساعد الجنيه'],
    hurting: ['hurting the pound', 'بيضغط على الجنيه'], steady: ['steady', 'ثابت'], no_data_short: ['no data yet', 'مفيش بيانات'],
    in_one_line: ['In one line', 'في سطر واحد'], right_now_t: ['Right now', 'دلوقتي'], why_matters: ['Why it matters for the pound', 'ليه مهم للجنيه'],
    what_next: ['What could happen next', 'إيه اللي ممكن يحصل'], affects: ['This affects', 'ده بيأثر على'], caused_by: ['Affected by', 'بيتأثر بـ'],
    see_numbers: ['See the numbers', 'شوف الأرقام'], next: ['Next', 'التالي'], back: ['Back', 'رجوع'], finish: ['Finish', 'خلصت'],
    step_of: ['Step', 'خطوة'], of: ['of', 'من'], lessons_title: ['Learn in 5 minutes', 'اتعلم في 5 دقايق'],
    lessons_hint: ['Short lessons that use today\'s real numbers. No jargon.', 'دروس قصيرة بأرقام النهارده الحقيقية ومن غير مصطلحات صعبة.'],
    min_read: ['min', 'دقيقة'], done: ['done', 'خلصته'], quiz: ['Quick check', 'سؤال سريع'], correct: ['Correct!', 'صح!'],
    not_quite: ['Not quite.', 'مش بالظبط.'], related_boxes: ['Related boxes in the chain', 'مربعات مرتبطة في السلسلة'],
    what_changed: ['What changed today', 'إيه اللي اتغير النهارده'], go_pro: ['Open the full Pro dashboard', 'افتح لوحة المحترفين'],
    big_dollar: ['1 US dollar', 'الدولار الواحد'], big_gold: ['Gold says the dollar is', 'دولار الدهب'], big_oil: ['Oil (Brent)', 'البترول'],
    pounds: ['pounds', 'جنيه'], per_barrel: ['per barrel', 'للبرميل'], tour_title: ['Guided tour', 'جولة سريعة'],
    layout: ['Layout', 'طريقة العرض'], lay_auto: ['Auto', 'تلقائي'], lay_mobile: ['Phone', 'موبايل'], lay_desktop: ['Desktop', 'كمبيوتر'],
    lay_hint: ['tap to switch', 'دوس للتغيير'], install: ['Install app', 'نزّل التطبيق'],
    help_ppi: ['Each sub-index compares today with the last 3 years (z-score → −100…+100), adds fired rules and decaying events. Weights: config/indices.yaml.',
      'كل مؤشر فرعي بيقارن النهارده بآخر 3 سنين، وبيضيف الإشارات والأحداث. الأوزان في ملف الإعدادات.'],
  };
  const DOMAIN_ICON = { hot: '⇅', fx: '£', monetary: '%', external: '⇄', fiscal: '§', energy: '◆', real: '↗', global: '◎', geo: '⌖', health: '✚' };
  const SUB_TO_DOMAIN = { external: 'external', monetary: 'monetary', fiscal: 'fiscal', commodities: 'energy', geopolitical: 'geo', global: 'global' };
  const DOMAIN_CHARTS = { hot: [], fx: ['fx'], monetary: ['cpi', 'real'], external: ['nir', 'remit', 'choke'], fiscal: [], energy: ['brent'],
    real: ['pmi'], global: [], geo: ['gpr', 'choke'], health: [] };
  const RULE_DOMAIN = { fx: 'fx', monetary: 'monetary', external: 'external', fiscal: 'fiscal', energy: 'energy', real: 'real',
    gold: 'energy', global: 'global', geopolitical: 'geo', healthcare: 'health' };
  const KPIS = ['fx_cbe_official', 'gold_gap_pct', 'nir', 'cpi_urban_yoy', 'cbe_odr', 'brent', 'egx30', 'pmi'];

  // ------------------------------------------------------------------ state
  const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  const S = {
    D: null, version: null, lang: store('pulse.lang') === 'ar' ? 'ar' : 'en', theme: store('pulse.theme') || 'auto',
    route: 'overview', sigFilter: 'fired', ranges: {}, seriesCache: {}, server: false, running: false, lastPoll: null,
    mode: store('pulse.mode') === 'pro' ? 'pro' : 'simple', tour: null,
    lessonsDone: new Set((store('pulse.lessons') || '').split(',').filter(Boolean)), lesson: null,
    L: null, liveFlash: new Set(), palIndex: 0, flashIds: new Set(), dataFilter: '', explain: store('pulse.explain') === '1',
  };
  const t = (k) => (I18N[k] ? I18N[k][S.lang === 'ar' ? 1 : 0] : k);
  const AR = () => S.lang === 'ar';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const nm = (o) => (AR() ? o.name_ar || o.name_en : o.name_en);
  // keep numbers/dates left-to-right inside Arabic sentences
  const bidi = (escaped) => escaped.replace(/([+\-−]?\d[\d,]*(?:\.\d+)?(?:[-:/]\d+)*%?)/g, '<span class="num">$1</span>');

  // ------------------------------------------------------------------ data loading (script injection = works on file://)
  function loadJs(src, cbName) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      const prev = window[cbName];
      window[cbName] = (payload) => { resolve(payload); };
      s.src = src + (src.includes('?') ? '&' : '?') + 't=' + Date.now();
      s.onerror = () => { reject(new Error('load failed: ' + src)); };
      s.onload = () => { setTimeout(() => { s.remove(); if (prev) window[cbName] = prev; }, 0); };
      document.head.appendChild(s);
    });
  }
  const loadBundle = () => loadJs('data/pulse-data.js', '__pulseData');
  const loadManifest = () => loadJs('data/manifest.js', '__pulseManifest');
  const loadLive = () => loadJs('data/live.js', '__pulseLive');
  async function loadSeries(id) {
    if (S.seriesCache[id] && S.seriesCache[id].version === S.version) return S.seriesCache[id];
    const p = await loadJs('data/series/' + encodeURIComponent(id) + '.js', '__pulseSeries');
    p.version = S.version;
    S.seriesCache[id] = p;
    return p;
  }

  // ------------------------------------------------------------------ formatting
  const NF = {};
  const nf = (v, d = 2) => { if (v == null || Number.isNaN(v)) return '—'; const k = d; NF[k] = NF[k] || new Intl.NumberFormat('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }); return NF[k].format(v); };
  function digitsFor(v, unit) {
    const a = Math.abs(v);
    if (unit === 'ratio') return 2;
    if (a >= 1000) return 0;
    if (a >= 100) return 1;
    return 2;
  }
  function unitShort(u) {
    const m = { 'EGP per USD': 'EGP', 'USD mn': 'mn $', 'USD bn': 'bn $', 'USD/bbl': '$/bbl', 'EGP/gram': 'EGP/g', 'USD/oz': '$/oz',
      'EGP/litre': 'EGP/L', '% GDP': '% GDP', 'points': 'pts', 'index': '', 'ratio': '×', 'pp': 'pp', '%': '%', 'code': '', 'score': '', 'tone': '' };
    return m[u] ?? u;
  }
  function valueHtml(s) { return s.value == null ? esc(t('no_data')) : `<span class="vu" dir="ltr">${valueInner(s)}</span>`; }
  function valueInner(s) {
    const u = s.unit;
    const d = digitsFor(s.value, u);
    if (u === '%') return `<span class="num">${nf(s.value, d)}%</span>`;
    if (u === 'pp') return `<span class="num">${s.value > 0 ? '+' : ''}${nf(s.value, 1)}</span><small>pp</small>`;
    const us = unitShort(u);
    return `<span class="num">${nf(s.value, d)}</span>${us ? ` <small>${esc(us)}</small>` : ''}`;
  }
  function changeInfo(s) {
    if (s.change == null) return null;
    const pctUnit = s.unit === '%' || s.unit === 'pp';
    const d = pctUnit ? 2 : digitsFor(s.prev ?? s.value, s.unit);
    const txt = `${s.change > 0 ? '+' : s.change < 0 ? '−' : '±'}${nf(Math.abs(s.change), d)}${pctUnit ? ' pp' : ''}` +
      (!pctUnit && s.change_pct != null && Math.abs(s.change_pct) < 1000 ? ` (${s.change_pct > 0 ? '+' : ''}${nf(s.change_pct, 1)}%)` : '');
    const dir = Math.sign(s.change) * (s.sign || 0);
    const cls = dir > 0 ? 'p' : dir < 0 ? 'r' : 'n';
    const arrow = s.change > 0 ? '▲' : s.change < 0 ? '▼' : '■';
    const word = dir > 0 ? t('pressure_word') : dir < 0 ? t('relief_word') : '';
    return { txt, cls, arrow, word };
  }
  function ago(iso) {
    if (!iso) return '';
    const ms = Date.now() - new Date(iso).getTime();
    const m = Math.round(ms / 60000);
    if (m < 2) return t('ago_now');
    if (m < 60) return AR() ? `من ${m} ${t('ago_min')}` : `${m} ${t('ago_min')}`;
    const h = Math.round(m / 60);
    if (h < 48) return AR() ? `من ${h} ${t('ago_h')}` : `${h} ${t('ago_h')}`;
    return AR() ? `من ${Math.round(h / 24)} ${t('ago_d')}` : `${Math.round(h / 24)} ${t('ago_d')}`;
  }
  function until(iso) {
    const ms = new Date(iso).getTime() - Date.now();
    if (ms < 0) return '';
    const m = Math.round(ms / 60000);
    if (m < 60) return `${t('in_')} ${m}m`;
    const h = Math.floor(m / 60);
    if (h < 48) return `${t('in_')} ${h}h ${m % 60}m`;
    return `${t('in_')} ${Math.round(h / 24)}d`;
  }
  const fmtDate = (iso) => { if (!iso) return ''; const d = new Date(iso + (iso.length === 10 ? 'T12:00:00' : ''));
    return d.toLocaleDateString(AR() ? 'ar-EG-u-nu-latn' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); };
  function fmtObs(iso, freq) {
    if (!iso) return '';
    const y = +iso.slice(0, 4), m = +iso.slice(5, 7);
    const mon = new Date(y, m - 1, 15).toLocaleDateString(AR() ? 'ar-EG-u-nu-latn' : 'en-GB', { month: 'short', year: 'numeric' });
    if (freq === 'monthly') return mon;
    if (freq === 'quarterly') return `Q${Math.floor((m - 1) / 3) + 1} ${y}`;
    if (freq === 'fiscal_year') return `FY${y}/${String(y + 1).slice(2)}`;
    if (freq === 'annual') return String(y);
    return fmtDate(iso);
  }
  const verdict = (v) => v == null ? ['n', t('no_data')] : v <= -40 ? ['r', t('strong_relief')] : v < -10 ? ['r', t('relief')] :
    v <= 10 ? ['n', t('balanced')] : v < 40 ? ['p', t('pressure')] : ['p', t('strong_pressure')];
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  // ------------------------------------------------------------------ small components
  function sparkSvg(points, cls = '') {
    if (!points || points.length < 2) return '<svg class="spark" aria-hidden="true"></svg>';
    const vals = points.map((p) => p[1]);
    const min = Math.min(...vals), max = Math.max(...vals), span = max - min || 1;
    const W = 200, H = 34, n = points.length;
    const xy = vals.map((v, i) => [(i / (n - 1)) * W, H - 3 - ((v - min) / span) * (H - 6)]);
    const d = xy.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
    const last = xy[xy.length - 1];
    return `<svg class="spark ${cls}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
      <path d="${d} L ${W} ${H} L 0 ${H} Z" fill="var(--brand)" opacity=".08"/>
      <path d="${d}" fill="none" stroke="var(--brand)" stroke-width="1.6" vector-effect="non-scaling-stroke"/>
      <circle cx="${last[0]}" cy="${last[1]}" r="2.6" fill="var(--sand)"/></svg>`;
  }
  const exTxt = (pair) => (pair ? (AR() ? pair[1] || pair[0] : pair[0]) : '');
  const firstSentence = (txt, n = 120) => { const m = (txt || '').match(/^.*?[.!؟?](\s|$)/); let x = m ? m[0].trim() : (txt || ''); return x.length > n ? x.slice(0, n - 1) + '…' : x; };
  function fmtChange(chg, pct, pp, unit) {
    if (chg == null) return '';
    const d = pp ? 2 : digitsFor(chg, unit);
    return `${chg > 0 ? '+' : chg < 0 ? '−' : '±'}${nf(Math.abs(chg), d)}${pp ? ' pp' : ''}${!pp && pct != null && Math.abs(pct) < 1000 ? ` (${pct > 0 ? '+' : ''}${nf(pct, 1)}%)` : ''}`;
  }
  // read the impact from the latest move, or from the level vs a threshold (gaps, changes, ratios)
  const impactDir = (s, moveChange) => (s.explain && s.explain.basis === 'level' && s.value != null) ? (s.value - (s.explain.pivot || 0)) : moveChange;
  const META_AR = { daily: 'يومي', weekly: 'أسبوعي', monthly: 'شهري', quarterly: 'ربع سنوي', fiscal_year: 'سنة مالية', annual: 'سنوي',
    per_auction: 'كل مزاد', event: 'عند الحدث', official: 'رسمي', secondary: 'مصدر صحفي', unofficial: 'غير رسمي', derived: 'محسوب',
    manual: 'يدوي', SCRAPE: 'من موقع المصدر', FREE_API: 'واجهة مجانية', FREE_FILE: 'ملف مجاني', MANUAL: 'إدخال يدوي', PAID: 'مدفوع', DERIVED: 'محسوب' };
  const meta = (x) => (AR() && META_AR[x] ? META_AR[x] : x);
  const EV_DOMAIN = { energy: 'commodities', gold: 'commodities', geopolitical: 'geopolitical', external: 'external', fiscal: 'fiscal', healthcare: 'healthcare', fx: 'fiscal', monetary: 'fiscal' };
  function explainPanel(s) {
    const ex = s.explain;
    if (!ex) return '';
    const w = s.window;
    const pp = s.unit === '%' || s.unit === 'pp';
    let happened = '';
    if (w && w.change != null && s.value != null) {
      const dir = w.change > 0 ? t('rose') : w.change < 0 ? t('fell') : t('flat');
      happened = `<p><span class="num">${esc(fmtObs(w.start_date, s.freq))}</span> → <span class="num">${esc(fmtObs(s.date, s.freq))}</span>: ${esc(dir)} <span class="num">${esc(w.change ? fmtChange(w.change, w.change_pct, pp, s.unit) : '')}</span>
        (${esc(t('from_'))} <span class="num">${nf(w.start_value, digitsFor(w.start_value, s.unit))}</span> ${esc(t('to_'))} <span class="num">${nf(s.value, digitsFor(s.value, s.unit))}</span>).</p>`;
    } else if (!s.empty) happened = `<p class="muted">${esc(t('no_history'))}</p>`;
    const moves = (s.moves || []).map((m) => {
      const r = S.D.series[m.id]; const dir = Math.sign(m.change) * (m.sign || 0);
      const cls = dir > 0 ? 'p' : dir < 0 ? 'r' : 'n';
      return `<li><a href="#/s/${m.id}" data-series="${m.id}">${esc(r ? nm(r) : m.id)}</a> <span class="t-chg ${cls}" style="display:inline-flex"><span class="num">${esc(fmtChange(m.change, m.change_pct, m.pp, m.unit))}</span></span>
        <span class="tiny muted num">${esc(fmtDate(m.from))} → ${esc(fmtDate(m.to))}</span>${m.url ? ` <a class="tiny" href="${esc(m.url)}" target="_blank" rel="noopener">${esc(t('source'))} ↗</a>` : ''}</li>`;
    }).join('');
    const sigs = S.D.rules.filter((r) => r.fired && (r.inputs || []).some((i) => i.series === s.id))
      .map((r) => `<li><b>${esc(r.id)}</b> — ${AR() ? bidi(esc(r.ar || r.en)) : esc(r.en)}</li>`).join('');
    const evd = EV_DOMAIN[s.domain];
    const evs = S.D.events.filter((e) => e.domain === evd && e.direction !== 0).slice(0, 3)
      .map((e) => `<li><span class="num">${esc(fmtDate(e.event_date))}</span> — ${esc(AR() ? e.title_ar || e.title_en : e.title_en)} <a class="tiny" href="${esc(e.source_url)}" target="_blank" rel="noopener">↗</a></li>`).join('');
    const ch = impactDir(s, w && w.change != null ? w.change : s.change);
    const up = `<b>${esc(t('if_rises'))}:</b> ${esc(exTxt(ex.up))}`, down = `<b>${esc(t('if_falls'))}:</b> ${esc(exTxt(ex.down))}`;
    const lead = ch > 0 ? `<p>${up}</p><p class="small muted">${down}</p>` : ch < 0 ? `<p>${down}</p><p class="small muted">${up}</p>` : `<p>${up}</p><p>${down}</p>`;
    return `<section class="card explain"><h3>${esc(t('what_means'))}</h3>
      <div class="ex-row"><b>${esc(t('what_is'))}</b><p>${esc(exTxt(ex.what))}</p></div>
      <div class="ex-row"><b>${esc(t('what_moves'))}</b><p>${esc(exTxt(ex.drivers))}</p></div>
      <div class="ex-row"><b>${esc(t('what_happened'))}</b>${happened}
        ${moves ? `<div class="small" style="margin-top:6px">${esc(t('alongside'))}:</div><ul class="inputs">${moves}</ul>` : ''}
        ${sigs ? `<div class="small" style="margin-top:8px">${esc(t('signals_using'))}:</div><ul class="inputs">${sigs}</ul>` : ''}
        ${evs ? `<div class="small" style="margin-top:8px">${esc(t('related_events'))}:</div><ul class="inputs">${evs}</ul>` : ''}
        ${moves || sigs || evs ? `<p class="tiny muted" style="margin-top:6px">${esc(t('not_proof'))}</p>` : ''}</div>
      <div class="ex-row"><b>${esc(t('may_lead'))}</b>${lead}</div></section>`;
  }
  function badges(s) {
    const out = [];
    if (s.quality) out.push(`<span class="pill ${s.quality === 'official' ? '' : 'sand'}">${esc(meta(s.quality))}</span>`);
    if (s.stale === 1) out.push(`<span class="pill warn">${esc(t('stale'))}</span>`);
    if (s.stale === 2) out.push(`<span class="pill crit">${esc(t('very_stale'))}</span>`);
    if (s.closed) out.push(`<span class="pill">${esc(t('closed'))}</span>`);
    if (s.conflict) out.push(`<span class="pill warn">${esc(t('conflict'))}</span>`);
    return out.join('');
  }
  function tile(id) {
    const s = S.D.series[id];
    if (!s) return '';
    const flash = S.flashIds.has(id) ? ' flash' : '';
    if (s.empty) {
      const hint = s.access === 'MANUAL' || s.access === 'PAID' ? t('manual_hint') : t('auto_hint');
      return `<button class="tile empty" data-series="${id}" title="${esc(hint)}"><span class="t-name">${esc(nm(s))}</span>
        <span class="t-val">${esc(t('no_data'))}</span><span class="t-meta">${esc(hint)}</span></button>`;
    }
    const ch = changeInfo(s);
    const what = s.explain ? exTxt(s.explain.what) : '';
    const idir = impactDir(s, s.change);
    const impact = s.explain && idir ? exTxt(idir > 0 ? s.explain.up : s.explain.down) : '';
    const exLines = S.explain && what ? `<span class="t-ex">${esc(firstSentence(what))}</span>` : '';
    const exImpact = S.explain && impact && impact !== '—' ? `<span class="t-ex t-imp">→ ${esc(firstSentence(impact, 140))}</span>` : '';
    return `<button class="tile${flash}${S.explain ? ' explained' : ''}" data-series="${id}" aria-label="${esc(nm(s))}" title="${esc(what)}">
      <span class="t-name">${esc(nm(s))}</span>${exLines}
      <span class="t-val">${valueHtml(s)}</span>
      ${ch ? `<span class="t-chg ${ch.cls}" title="${esc(ch.word)}" dir="ltr"><span aria-hidden="true">${ch.arrow}</span><span class="num">${esc(ch.txt)}</span></span>` : '<span class="t-chg n">&nbsp;</span>'}
      ${exImpact}${sparkSvg(s.spark)}
      <span class="t-meta"><span class="num">${esc(fmtObs(s.date, s.freq))}</span>${badges(s)}</span></button>`;
  }
  function gaugeSvg(v) {
    const ang = v == null ? 0 : Math.max(-100, Math.min(100, v)) / 100 * 90;
    const ticks = [-100, -50, 0, 50, 100].map((x) => {
      const a = (x / 100 * 90 - 90) * Math.PI / 180;
      const r1 = 104, r2 = 112;
      return `<line x1="${120 + r1 * Math.cos(a)}" y1="${120 + r1 * Math.sin(a)}" x2="${120 + r2 * Math.cos(a)}" y2="${120 + r2 * Math.sin(a)}" stroke="var(--border-strong)" stroke-width="2"/>`;
    }).join('');
    return `<svg class="gauge" viewBox="0 0 240 132" dir="ltr" role="img" aria-label="${esc(t('ppi'))} ${v == null ? '' : v}">
      <defs><linearGradient id="gg" x1="0" x2="1"><stop offset="0" stop-color="var(--relief)"/><stop offset=".5" stop-color="var(--neutral)"/>
      <stop offset="1" stop-color="var(--pressure)"/></linearGradient></defs>
      <path d="M 24 120 A 96 96 0 0 1 216 120" fill="none" stroke="url(#gg)" stroke-width="16" stroke-linecap="round"/>
      ${ticks}
      <g class="needle" style="transform: rotate(${ang}deg)"><line x1="120" y1="120" x2="120" y2="38" stroke="var(--text)" stroke-width="3.5" stroke-linecap="round"/></g>
      <circle cx="120" cy="120" r="8" fill="var(--text)"/><circle cx="120" cy="120" r="3" fill="var(--surface)"/>
      <text x="16" y="131" font-size="10" fill="var(--text-2)">−100</text><text x="206" y="131" font-size="10" fill="var(--text-2)">+100</text></svg>`;
  }
  function dbar(v, posVar = '--pressure', negVar = '--relief') {
    if (v == null) return '<div class="dbar" dir="ltr"></div>';
    const w = Math.min(100, Math.abs(v)) / 2;
    const style = v >= 0 ? `left:50%;width:${w}%;background:var(${posVar})` : `left:${50 - w}%;width:${w}%;background:var(${negVar})`;
    return `<div class="dbar" dir="ltr"><span style="${style}"></span></div>`;
  }
  function sigCard(r, compact = false) {
    const cls = !r.fired ? '' : r.direction > 0 ? 'p' : r.direction < 0 ? 'r' : 'n';
    const word = r.direction > 0 ? t('pressure_word') : r.direction < 0 ? t('relief_word') : t('note_word');
    const bars = [0.2, 0.4, 0.6, 0.8, 1].map((x) => `<i class="${r.strength >= x - 1e-9 ? 'on' : ''}"></i>`).join('');
    const text = AR() ? (r.ar || r.en) : r.en;
    const learn = r.learn ? `<div class="learn"><b>${esc(t('learn'))} · ${esc(r.concept)}</b><br>${esc(AR() ? r.learn[1] : r.learn[0])}</div>` : '';
    const inputs = (r.inputs || []).map((i) => {
      if (i.series) {
        const s = S.D.series[i.series];
        const label = s ? nm(s) : i.series;
        const v = typeof i.value === 'number' ? nf(i.value, digitsFor(i.value, s && s.unit)) : i.value;
        return `<li><a href="#/s/${i.series}" data-series="${i.series}">${esc(label)}</a> = <span class="num">${esc(v)}</span> · ${esc(i.source || '')} · <span class="num">${esc(i.obs_date || '')}</span></li>`;
      }
      return `<li>${esc(i.event || i.calendar || '')} · <span class="num">${esc(i.date || '')}</span>${i.url ? ` · <a href="${esc(i.url)}" target="_blank" rel="noopener">↗</a>` : ''}</li>`;
    }).join('');
    const body = r.evaluable
      ? `<p>${AR() ? bidi(esc(text || '')) : esc(text || '')}</p>`
      : `<p class="muted small">${esc(t('missing'))}: ${esc((r.missing || []).join(', '))}</p>`;
    return `<article class="sig ${cls}" dir="auto">
      <div class="sig-head"><b>${esc(r.id)}</b><span class="pill">${esc(r.name || '')}</span>
        ${r.fired ? `<span class="pill ${cls === 'p' ? 'p' : cls === 'r' ? 'r' : 'sand'}">${esc(word)}</span><span class="strength" title="${esc(t('strength'))} ${r.strength}">${bars}</span>` : ''}
        ${!r.evaluable ? `<span class="pill">${esc(t('not_evaluable'))}</span>` : ''}</div>
      ${body}
      ${compact ? '' : `<details class="more"><summary>${esc(t('learn'))} · ${esc(t('inputs'))}</summary>${learn}
        ${inputs ? `<ul class="inputs">${inputs}</ul>` : ''}
        <div class="tiny muted" style="margin-top:6px">${esc(r.concept || '')} · ${esc(r.lag || '')} · ${esc(t('tool_default'))}</div></details>`}
    </article>`;
  }

  // ------------------------------------------------------------------ charts (Plotly)
  const CHARTS = {
    fx: { title: 'chart_fx', range: '1Y', series: ['fx_cbe_official', 'fx_gold_implied', 'fx_market'], build: (H) => [
      line(H.fx_market, t('market'), '--s3', { dash: 'dot', width: 1.5 }), line(H.fx_cbe_official, t('official'), '--s1'),
      { ...line(H.fx_gold_implied, t('gold_implied'), '--s2'), mode: 'lines+markers', marker: { size: 8, color: css('--s2'), line: { width: 2, color: css('--surface') } } }] },
    real: { title: 'chart_real', range: '3Y', series: ['real_headline', 'real_core'], zero: true, build: (H) => [
      line(H.real_headline, t('vs_urban'), '--s1', { shape: 'hv' }), line(H.real_core, t('vs_core'), '--s2', { shape: 'hv' }),
      { ...line(H.real_expected, t('vs_cbe'), '--s3'), mode: 'markers', marker: { size: 9, color: css('--s3') } }] },
    cpi: { title: 'chart_cpi', range: '3Y', series: ['cpi_urban_yoy', 'cpi_core_yoy', 'cbe_odr'], build: (H) => [
      line(H.cpi_urban_yoy, t('urban_cpi'), '--s1'), line(H.cpi_core_yoy, t('core_cpi'), '--s2'),
      line(extendStep(H.cbe_odr), t('deposit_rate'), '--s3', { shape: 'hv' })] },
    nir: { title: 'chart_nir', range: 'All', series: ['nir'], build: (H) => [line(scale(H.nir, 1 / 1000), t('chart_nir'), '--s1')] },
    brent: { title: 'chart_brent', range: '1Y', series: ['brent', 'brent_fut', 'budget_oil_assumption'], build: (H) => [
      line(H.brent, t('spot'), '--s1'), line(H.brent_fut, t('futures'), '--s2')],
      shapes: (H) => { const b = (H.budget_oil_assumption || []).slice(-1)[0]; return b ? [hline(b[1], '--critical', t('budget') + ' $' + b[1])] : []; } },
    choke: { title: 'chart_choke', range: '1Y', series: ['suez_ratio_7dma', 'hormuz_ratio_7dma'], build: (H) => [
      line(H.suez_ratio_7dma, 'Suez', '--s1'), line(H.babelmandeb_ratio_7dma, 'Bab el-Mandeb', '--s2'), line(H.hormuz_ratio_7dma, 'Hormuz', '--s3')],
      shapes: () => [hline(1, '--muted', t('baseline')), hline(0.6, '--critical', t('weak'), 'dot')] },
    remit: { title: 'chart_remit', range: 'All', series: ['remittances'], build: (H) => [{ type: 'bar', name: t('chart_remit'),
      x: (H.remittances || []).map((p) => p[0]), y: (H.remittances || []).map((p) => p[1]), marker: { color: css('--s1') },
      hovertemplate: '%{y:.2f} bn<extra></extra>' }] },
    gpr: { title: 'chart_gpr', range: '1Y', series: ['gpr_daily'], build: (H) => [
      { ...line(H.gpr_daily, t('daily'), '--s1', { width: 1 }), opacity: 0.35 }, line(rolling(H.gpr_daily, 7), t('avg7'), '--s1')] },
    pmi: { title: 'chart_pmi', range: 'All', series: ['pmi'], build: (H) => [{ ...line(H.pmi, 'PMI', '--s1'), mode: 'lines+markers', marker: { size: 8 } }],
      shapes: () => [hline(50, '--muted', '50')] },
  };
  function line(pts, name, colorVar, o = {}) {
    pts = pts || [];
    return { type: 'scatter', mode: 'lines', name, x: pts.map((p) => p[0]), y: pts.map((p) => p[1]),
      line: { color: css(colorVar), width: o.width || 2, dash: o.dash, shape: o.shape || 'linear' },
      hovertemplate: '%{y:,.2f}<extra>' + esc(name) + '</extra>' };
  }
  const scale = (pts, k) => (pts || []).map((p) => [p[0], p[1] * k]);
  const extendStep = (pts) => { if (!pts || !pts.length) return pts; const last = pts[pts.length - 1]; return [...pts, [S.D.as_of, last[1]]]; };
  function rolling(pts, n) { if (!pts) return []; const out = []; let sum = 0; for (let i = 0; i < pts.length; i++) { sum += pts[i][1]; if (i >= n) sum -= pts[i - n][1]; if (i >= n - 1) out.push([pts[i][0], sum / n]); } return out; }
  function hline(y, colorVar, label, dash = 'dash') {
    return { type: 'line', xref: 'paper', x0: 0, x1: 1, y0: y, y1: y, line: { color: css(colorVar), width: 1.3, dash }, label: { text: label, textposition: 'start', font: { size: 10, color: css('--text-2') } } };
  }
  function baseLayout(extra = {}) {
    return Object.assign({
      margin: { l: 46, r: 14, t: 8, b: 34 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: getComputedStyle(document.body).fontFamily, size: 12, color: css('--text-2') },
      hovermode: 'x unified', hoverlabel: { bgcolor: css('--surface'), bordercolor: css('--border'), font: { color: css('--text') } },
      legend: { orientation: 'h', y: 1.14, x: 0, font: { size: 11.5 } },
      xaxis: { gridcolor: 'rgba(0,0,0,0)', linecolor: css('--border'), tickfont: { size: 11 } },
      yaxis: { gridcolor: css('--border'), zeroline: false, tickfont: { size: 11 } },
    }, extra);
  }
  function rangeStart(r) {
    if (r === 'All') return null;
    const d = new Date(S.D.as_of + 'T12:00:00');
    const m = { '1M': 1, '3M': 3, '6M': 6, '1Y': 12, '3Y': 36, '5Y': 60 }[r];
    d.setMonth(d.getMonth() - m);
    return d.toISOString().slice(0, 10);
  }
  const RANGES = ['1M', '3M', '6M', '1Y', '3Y', 'All'];
  function rangeBar(key, cur) {
    return `<div class="rangebar" role="group" aria-label="range">${RANGES.map((r) => `<button type="button" data-range="${r}" data-chart="${key}" aria-pressed="${r === cur}">${r === 'All' ? (AR() ? 'الكل' : 'All') : r}</button>`).join('')}</div>`;
  }
  function chartCard(key, tall = false) {
    const c = CHARTS[key];
    const cur = S.ranges[key] || c.range;
    const caps = c.series.map((id) => { const s = S.D.series[id]; return s && !s.empty ? `${nm(s)}: ${s.source} · ${fmtDate(s.date)}` : null; }).filter(Boolean);
    return `<section class="card"><h3>${esc(t(c.title))}${rangeBar(key, cur)}</h3><div class="chart${tall ? ' tall' : ''}" dir="ltr" id="ch_${key}" data-chartkey="${key}"></div>
      <div class="cap">${esc(t('source'))}: ${esc(caps.join(' · '))}</div></section>`;
  }
  function drawChart(key) {
    const el = document.getElementById('ch_' + key);
    if (!el || !window.Plotly) return;
    const c = CHARTS[key];
    const H = S.D.history;
    const traces = c.build(H).filter((tr) => tr.x && tr.x.length);
    const start = rangeStart(S.ranges[key] || c.range);
    const shapes = c.shapes ? c.shapes(H) : [];
    if (c.zero) shapes.push(hline(0, '--muted', ''));
    const layout = baseLayout({ shapes, showlegend: traces.length > 1 });
    if (start) layout.xaxis.range = [start, S.D.as_of];
    if (start) layout.yaxis.autorange = true;
    Plotly.react(el, traces, layout, { displayModeBar: false, responsive: true });
    if (start) autoY(el, traces, start);
  }
  function autoY(el, traces, start) {
    let lo = Infinity, hi = -Infinity;
    traces.forEach((tr) => tr.x.forEach((x, i) => { if (x >= start && tr.y[i] != null) { lo = Math.min(lo, tr.y[i]); hi = Math.max(hi, tr.y[i]); } }));
    const lay = el.layout || {};
    (lay.shapes || []).forEach((s) => { if (s.y0 != null && s.xref === 'paper') { lo = Math.min(lo, s.y0); hi = Math.max(hi, s.y0); } });
    if (lo < hi) { const pad = (hi - lo) * 0.08; Plotly.relayout(el, { 'yaxis.range': [lo - pad, hi + pad] }); }
  }
  function drawAllCharts() { $$('[data-chartkey]').forEach((el) => drawChart(el.dataset.chartkey)); }

  // ------------------------------------------------------------------ live layer (intraday, ~15 min)
  const LIVE_SERIES = { usd_egp: 'fx_market', egx30: 'egx30', brent: 'brent_fut', gold: 'xauusd', dxy: 'dxy', vix: 'vix',
    us10y: 'us10y', wheat: 'wheat', gas_eu: 'ttf_fut', em_eq: 'msci_em_proxy', cib: 'cib_local', cib_gdr: 'cib_gdr' };
  function timeOnly(iso) { return iso ? iso.slice(11, 16) : ''; }
  function liveSection(compact) {
    const L = S.L;
    if (!L) return '';
    if (compact === undefined) compact = S.mode === 'simple' && S.route === 'home';
    const KEY = ['usd_egp', 'egx30', 'brent', 'gold'];
    const qs = compact ? KEY.map((k) => L.quotes.find((q) => q.id === k)).filter(Boolean) : L.quotes;
    const chips = qs.map((q) => {
      const dir = Math.sign(q.chg || 0) * (q.sign || 0);
      const cls = dir > 0 ? 'p' : dir < 0 ? 'r' : 'n';
      const arrow = (q.chg || 0) > 0 ? '▲' : (q.chg || 0) < 0 ? '▼' : '■';
      const sid = LIVE_SERIES[q.id];
      return `<button class="lq${S.liveFlash.has(q.id) ? ' flash' : ''}" ${sid ? `data-series="${sid}"` : ''} title="${esc(q.source)} · ${esc(q.ts)}">
        <span class="lq-n">${esc(AR() ? q.name_ar : q.name_en)}</span>
        <span class="lq-v num">${nf(q.price, q.digits)}<small>${esc(q.unit)}</small></span>
        <span class="t-chg ${cls}"><span aria-hidden="true">${arrow}</span><span class="num">${q.chg_pct == null ? '—' : (q.chg_pct > 0 ? '+' : '') + nf(q.chg_pct, 2) + '%'}</span></span>
        ${sparkSvg(q.spark)}
        <span class="lq-t"><span class="pill ${q.open ? 'live-on' : ''}">${esc(q.open ? t('open_mkt') : t('closed_mkt'))}</span> <span class="num">${esc(q.open ? timeOnly(q.ts) : fmtDate(q.ts.slice(0, 10)))}</span></span></button>`;
    }).join('');
    const IMPORTANT = ['gold_gap', 'oil_gap', 'hot_money', 'egx', 'market_gap', 'risk', 'gold_world'];
    const ins = compact ? [...L.insights].sort((a, b) => IMPORTANT.indexOf(a.id) - IMPORTANT.indexOf(b.id)).slice(0, 3) : L.insights;
    const reads = ins.map((i) => {
      const cls = i.dir > 0 ? 'p' : i.dir < 0 ? 'r' : 'n';
      const src = (i.sources || []).map((x) => `<a href="${esc(x.url)}" target="_blank" rel="noopener"><bdi>${esc(x.name)}</bdi></a>${x.at ? ` <span class="num">${esc(timeOnly(x.at))}</span>` : ''}`).join(' · ');
      return `<div class="sig ${cls}"><p>${AR() ? bidi(esc(i.ar)) : esc(i.en)}</p><div class="tiny muted" style="margin-top:4px">${src}</div></div>`;
    }).join('');
    const news = (L.news || []).slice(0, compact ? 3 : 6).map((n) => `<li><a dir="auto" href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.title)}</a>
      <span class="tiny muted">${esc(n.outlet)} · ${esc(ago(n.at))}</span></li>`).join('');
    const cbe = L.cbe ? `<div class="mini"><span class="muted small">${esc(t('cbe_today'))}</span><b class="num">${nf(L.cbe.buy, 4)}</b>
      <span class="tiny muted">${esc(fmtDate(L.cbe.date))} · <a href="${esc(L.cbe.url)}" target="_blank" rel="noopener">CBE ↗</a></span></div>` : '';
    const gold = L.gold_eg ? `<div class="mini"><span class="muted small">${esc(t('gold21_now'))}</span><b class="num">${nf(L.gold_eg.k21, 0)} EGP</b>
      <span class="tiny muted"><span class="num">${esc(timeOnly(L.gold_eg.ts))}</span> · <a href="${esc(L.gold_eg.url)}" target="_blank" rel="noopener">banklive ↗</a></span></div>` : '';
    return `<section class="card live-card"><h3><span><span class="live-dot"></span>${esc(t('right_now'))}</span>
        <span class="tiny muted">${esc(t('prices_updated'))} ${esc(ago(L.generated))} · <span class="num">${esc(timeOnly(L.generated))}</span> Cairo</span></h3>
      <div class="lq-row">${chips}</div>
      <div class="grid g-live">
        <div><div class="small muted" style="margin:10px 0 6px">${esc(t('live_reads'))}</div><div class="story">${reads}</div></div>
        <div><div class="minis">${cbe}${gold}</div><div class="small muted" style="margin:12px 0 6px">${esc(t('headlines'))}</div><ul class="news">${news}</ul></div>
      </div>
      ${ins.length > 2 ? `<button class="btn more-btn" type="button" data-more="1">${esc(AR() ? 'اعرض كل القراءات' : 'Show all live reads')} (${ins.length})</button>` : ''}
      <p class="tiny muted" style="margin:8px 0 0">${esc(t('live_note'))}</p></section>`;
  }
  async function pollLive(announce) {
    try {
      const L = await loadLive();
      const old = S.L;
      S.L = L;
      if (old && old.generated !== L.generated) {
        S.liveFlash = new Set(L.quotes.filter((q) => { const o = old.quotes.find((x) => x.id === q.id); return o && o.price !== q.price; }).map((q) => q.id));
        { const el = $('#liveSlot'); if (el) el.innerHTML = liveSection(); }
        priceBar();
        setTimeout(() => { S.liveFlash = new Set(); }, 2500);
      }
      S.lastPoll = Date.now();
      priceBar();
    } catch (e) { /* live.js not published yet */ }
    updateLive();
  }

  // ------------------------------------------------------------------ SIMPLE MODE (tutor)
  const ST = { '-1': ['r', 'helping'], '1': ['p', 'hurting'], '0': ['n', 'steady'], 'null': ['x', 'no_data_short'] };
  const stOf = (n) => ST[String(n.status)] || ST.null;
  const L2 = (pair) => (pair ? (AR() ? pair[1] || pair[0] : pair[0]) : '');
  const nodeById = (id) => (S.D.chain ? S.D.chain.nodes.find((n) => n.id === id) : null);

  function chainCard(n) {
    const [cls, key] = stOf(n);
    return `<button class="cn cn-${cls}" data-node="${n.id}">
      <span class="cn-ic" aria-hidden="true">${n.icon}</span>
      <span class="cn-body"><span class="cn-t">${esc(L2(n.title))}</span>
      <span class="cn-v">${bidi(esc(L2(n.value) || '—'))}</span>
      <span class="cn-s">${cls === 'p' ? '▲' : cls === 'r' ? '▼' : '•'} ${esc(t(key))}</span></span></button>`;
  }
  function chainMap() {
    const C = S.D.chain;
    if (!C) return '';
    const row = (id) => C.nodes.filter((n) => n.row === id).map(chainCard).join('');
    const title = (id) => esc(L2(C.rows.find((r) => r.id === id).title));
    const arrow = (txt) => `<div class="cn-arrow"><span aria-hidden="true">↓</span>${txt ? `<em>${esc(txt)}</em>` : ''}</div>`;
    return `<section class="card chain"><h3>${esc(t('chain_title'))}<button class="btn primary" data-tour="start" type="button">▶ ${esc(t('start_tour'))}</button></h3>
      <p class="small muted" style="margin-top:-4px">${esc(t('chain_hint'))}</p>
      <div class="cn-row"><div class="cn-label">${title(0)}</div><div class="cn-grid">${row(0)}</div></div>
      ${arrow(AR() ? 'بتأثر على الدولارات الداخلة والخارجة' : 'shake the flows of dollars')}
      <div class="cn-two">
        <div class="cn-row cn-in"><div class="cn-label">⬇ ${title(1)}</div><div class="cn-grid">${row(1)}</div></div>
        <div class="cn-row cn-out"><div class="cn-label">⬆ ${title(2)}</div><div class="cn-grid">${row(2)}</div></div>
      </div>
      ${arrow(AR() ? 'الفرق بينهم بيحدد' : 'the balance between them decides')}
      <div class="cn-row"><div class="cn-label">${title(3)}</div><div class="cn-grid cn-2">${row(3)}</div></div>
      ${arrow(AR() ? 'وده بيوصل لـ' : 'which flows into')}
      <div class="cn-row"><div class="cn-label">${title(4)}</div><div class="cn-grid cn-2">${row(4)}</div></div>
      ${arrow(AR() ? 'وفي الآخر' : 'and finally')}
      <div class="cn-row"><div class="cn-label">${title(5)}</div><div class="cn-grid cn-1">${row(5)}</div></div>
    </section>`;
  }
  function lessonsRow(full = false) {
    const ls = S.D.lessons || [];
    const card = (l) => `<a class="lesson${S.lessonsDone.has(l.id) ? ' done' : ''}" href="#/learn/${l.id}">
      <span class="ls-ic" aria-hidden="true">${l.icon}</span><span class="ls-t">${esc(L2(l.title))}</span>
      <span class="ls-m">${l.minutes} ${esc(t('min_read'))}${S.lessonsDone.has(l.id) ? ' · ✓ ' + esc(t('done')) : ''}</span></a>`;
    return `<section class="card"><h3>${esc(t('lessons_title'))}<span class="pill">${S.lessonsDone.size}/${ls.length} ✓</span></h3>
      <p class="small muted" style="margin-top:-4px">${esc(t('lessons_hint'))}</p>
      <div class="lessons ${full ? 'full' : ''}">${ls.map(card).join('')}</div></section>`;
  }
  function bigNumbers() {
    const fx = S.L && S.L.cbe ? S.L.cbe.buy : (S.D.series.fx_cbe_official || {}).value;
    const gq = S.D.series.fx_gold_implied || {};
    const bq = S.L ? (S.L.quotes || []).find((q) => q.id === 'brent') : null;
    const oil = bq ? bq.price : (S.D.series.brent_fut || {}).value;
    const big = (label, val, unit, sub) => `<div class="bign"><span class="bn-l">${esc(label)}</span><span class="bn-v num" dir="ltr">${val}</span>
      <span class="bn-u">${esc(unit)}</span>${sub ? `<span class="bn-s">${sub}</span>` : ''}</div>`;
    const gap = gq.value && fx ? (gq.value / fx - 1) * 100 : null;
    return `<div class="bigs">
      ${big(t('big_dollar'), fx ? nf(fx, 2) : '—', t('pounds'), AR() ? 'السعر الرسمي للبنك المركزي' : 'official CBE rate')}
      ${big(t('big_gold'), gq.value ? nf(gq.value, 2) : '—', t('pounds'), gap == null ? '' : `<span class="num">${gap > 0 ? '+' : ''}${nf(gap, 1)}%</span> ${AR() ? (Math.abs(gap) < 3 ? '— طبيعي' : '— انتبه') : (Math.abs(gap) < 3 ? '— normal' : '— watch')}`)}
      ${big(t('big_oil'), oil ? '$' + nf(oil, 0) : '—', t('per_barrel'), AR() ? 'مقابل <span class="num">75</span> دولار في الموازنة' : 'vs $75 in the budget')}
    </div>`;
  }
  function viewHome() {
    const D = S.D, h = D.headline || {};
    const [vc] = verdict(D.ppi.value);
    const changes = D.rules.filter((r) => r.fired && r.direction !== 0).sort((a, b) => b.strength - a.strength).slice(0, 4)
      .map((r) => `<li class="${r.direction > 0 ? 'p' : 'r'}">${AR() ? bidi(esc(r.ar || r.en)) : esc(r.en)}</li>`).join('');
    return `<div class="view simple">
      <section class="hero2 verdict-bg-${vc}">
        <div class="eyebrow">${esc(fmtDate(D.as_of))} · ${esc(t('ppi'))} <span class="num">${D.ppi.value == null ? '—' : (D.ppi.value > 0 ? '+' : '') + nf(D.ppi.value, 0)}/100</span></div>
        <h1 class="h2-sent">${esc(AR() ? h.ar : h.en)}</h1>
        ${(AR() ? h.good_ar : h.good_en) ? `<p class="h2-good">${esc(AR() ? h.good_ar : h.good_en)}</p>` : ''}
        ${bigNumbers()}
      </section>
      ${chainMap()}
      <div id="liveSlot" class="simple-live">${liveSection()}</div>
      ${lessonsRow()}
      ${changes ? `<section class="card"><h3>${esc(t('what_changed'))}</h3><ul class="changes">${changes}</ul></section>` : ''}
      <p style="text-align:center;margin:22px 0"><button class="btn" type="button" data-mode="pro">⚙ ${esc(t('go_pro'))}</button></p>
      <p class="disclaimer">${esc(t('disclaimer'))}</p></div>`;
  }
  function viewLearn() {
    return `<div class="view simple"><div class="page-head"><div><h1>${esc(t('lessons_title'))}</h1><p>${esc(t('lessons_hint'))}</p></div></div>
      ${lessonsRow(true)}${chainMap()}</div>`;
  }
  function viewLiveSimple() { return `<div class="view simple"><div id="liveSlot">${liveSection()}</div></div>`; }

  // node tutor card (opens in the side panel); in tour mode it shows Back/Next
  function openNode(id) {
    const n = nodeById(id);
    if (!n) return;
    const C = S.D.chain;
    const [cls, key] = stOf(n);
    const out = C.edges.filter((e) => e.from === id), inn = C.edges.filter((e) => e.to === id);
    const chip = (nid, label, dir) => { const m = nodeById(nid); if (!m) return ''; const [c2] = stOf(m);
      return `<button class="ch-chip cn-${c2}" data-node="${nid}">${dir === 'out' ? '→' : '←'} ${esc(L2(m.title))} <em>${esc(L2(label))}</em></button>`; };
    const srcs = (n.sources || []).map((x) => x.url ? `<a href="${esc(x.url)}" target="_blank" rel="noopener"><bdi>${esc(x.name)}</bdi></a> <span class="num">${esc(x.date || '')}</span>` : esc(x.name)).join(' · ');
    const nums = (n.series || []).filter((sid) => S.D.series[sid]).map((sid) => { const sr = S.D.series[sid];
      return `<button class="mini-tile" data-series="${sid}"><span>${esc(nm(sr))}</span><b class="num">${sr.empty ? '—' : valueHtml(sr)}</b></button>`; }).join('');
    let tourBar = '';
    if (S.tour) {
      const i = S.tour.i, N = C.tour.length;
      tourBar = `<div class="tourbar"><span class="small muted">${esc(t('tour_title'))} · ${esc(t('step_of'))} ${i + 1} ${esc(t('of'))} ${N}</span>
        <div class="tour-dots">${C.tour.map((_, k) => `<i class="${k === i ? 'on' : k < i ? 'past' : ''}"></i>`).join('')}</div>
        <div style="display:flex;gap:8px"><button class="btn" data-tour="back" ${i === 0 ? 'disabled' : ''}>${esc(t('back'))}</button>
        <button class="btn primary" data-tour="${i === N - 1 ? 'end' : 'next'}">${esc(i === N - 1 ? t('finish') : t('next'))} →</button></div></div>`;
    }
    $('#drawerBody').innerHTML = `${tourBar}
      <div class="node-head cn-${cls}"><span class="cn-ic big" aria-hidden="true">${n.icon}</span><div>
        <h2 class="d-title" id="drawerTitle">${esc(L2(n.title))}</h2>
        <div><span class="pill ${cls === 'p' ? 'p' : cls === 'r' ? 'r' : ''}">${esc(t(key))}</span> <b style="margin-inline-start:6px">${bidi(esc(L2(n.value) || ''))}</b></div></div></div>
      <div class="tutor">
        <div class="tu"><b>${esc(t('in_one_line'))}</b><p>${esc(L2(n.one))}</p></div>
        <div class="tu tu-now"><b>${esc(t('right_now_t'))}</b><p>${AR() ? bidi(esc(L2(n.now))) : esc(L2(n.now)) || '—'}</p>${srcs ? `<div class="tiny muted">${esc(t('source'))}: ${srcs}</div>` : ''}</div>
        <div class="tu"><b>${esc(t('why_matters'))}</b><p>${esc(L2(n.why))}</p></div>
        <div class="tu"><b>${esc(t('what_next'))}</b><p>${esc(L2(n.next))}</p></div>
        ${out.length ? `<div class="tu"><b>${esc(t('affects'))}</b><div class="chips2">${out.map((e) => chip(e.to, e.label, 'out')).join('')}</div></div>` : ''}
        ${inn.length ? `<div class="tu"><b>${esc(t('caused_by'))}</b><div class="chips2">${inn.map((e) => chip(e.from, e.label, 'in')).join('')}</div></div>` : ''}
        ${nums ? `<div class="tu"><b>${esc(t('see_numbers'))}</b><div class="mini-tiles">${nums}</div></div>` : ''}
      </div>`;
    const dr = $('#drawer'); dr.classList.add('open'); dr.setAttribute('aria-hidden', 'false');
    $('#drawer .drawer-panel').scrollTop = 0;
  }
  function tourGo(i) {
    const T = S.D.chain.tour;
    if (i < 0 || i >= T.length) { S.tour = null; closeDrawer(); return; }
    S.tour = { i };
    openNode(T[i]);
  }

  // lessons reader
  function viewLesson(id) {
    const l = (S.D.lessons || []).find((x) => x.id === id);
    if (!l) return viewLearn();
    const st = S.lesson && S.lesson.id === id ? S.lesson : (S.lesson = { id, i: 0, picked: null });
    const N = l.steps.length;
    const dots = Array.from({ length: N + 1 }, (_, k) => `<i class="${k === st.i ? 'on' : k < st.i ? 'past' : ''}"></i>`).join('');
    let body;
    if (st.i < N) {
      body = `<p class="lesson-step">${AR() ? bidi(esc(L2(l.steps[st.i]))) : esc(L2(l.steps[st.i]))}</p>`;
    } else {
      const q = l.quiz;
      const opts = q.options.map((o, k) => {
        let cls = '';
        if (st.picked != null) cls = k === q.answer ? 'right' : (k === st.picked ? 'wrong' : '');
        return `<button class="qopt ${cls}" data-quiz="${k}" ${st.picked != null ? 'disabled' : ''}>${esc(L2(o))}</button>`;
      }).join('');
      const fb = st.picked == null ? '' : `<p class="qfb ${st.picked === q.answer ? 'right' : 'wrong'}"><b>${esc(st.picked === q.answer ? t('correct') : t('not_quite'))}</b> ${esc(L2(q.why))}</p>`;
      body = `<div class="small muted">${esc(t('quiz'))}</div><p class="lesson-step">${esc(L2(q.q))}</p><div class="qopts">${opts}</div>${fb}`;
    }
    const rel = (l.nodes || []).map((nid) => { const m = nodeById(nid); return m ? `<button class="ch-chip cn-${stOf(m)[0]}" data-node="${nid}">${m.icon} ${esc(L2(m.title))}</button>` : ''; }).join('');
    const last = st.i === N;
    return `<div class="view simple"><p><a href="#/learn">← ${esc(t('lessons_title'))}</a></p>
      <section class="card lesson-card"><div class="ls-head"><span class="ls-ic big" aria-hidden="true">${l.icon}</span><h1>${esc(L2(l.title))}</h1></div>
        <div class="tour-dots">${dots}</div>${body}
        <div class="lesson-nav"><button class="btn" data-lstep="back" ${st.i === 0 ? 'disabled' : ''}>${esc(t('back'))}</button>
          ${last ? (st.picked != null ? `<a class="btn primary" href="#/learn">${esc(t('finish'))} ✓</a>` : '') : `<button class="btn primary" data-lstep="next">${esc(t('next'))} →</button>`}</div>
      </section>
      ${rel ? `<section class="card"><h3>${esc(t('related_boxes'))}</h3><div class="chips2">${rel}</div></section>` : ''}</div>`;
  }

  // ------------------------------------------------------------------ views
  function viewOverview() {
    const D = S.D;
    const p = D.ppi;
    const [vc, vtxt] = verdict(p.value);
    const subs = D.subindices.map((s) => `<button class="sub" data-route="d/${SUB_TO_DOMAIN[s.id]}" title="${esc(t('coverage'))} ${s.coverage_pct}%">
        <span class="nm">${esc(AR() ? s.name_ar : s.name_en)} <small class="num">${s.weight}%</small></span>${dbar(s.value)}
        <span class="val num">${s.value == null ? '—' : (s.value > 0 ? '+' : '') + Math.round(s.value)}<small>${Math.round(s.coverage_pct)}%</small></span></button>`).join('');
    const extra = D.extra.map((x) => `<div class="sub" style="cursor:default"><span class="nm">${esc(t(x.id === 'inflation' ? 'inflation_idx' : 'growth_idx'))}</span>
        ${dbar(x.value, '--s2', '--s3')}<span class="val num">${x.value == null ? '—' : (x.value > 0 ? '+' : '') + Math.round(x.value)}<small>${Math.round(x.coverage_pct)}%</small></span></div>`).join('');
    const fired = D.rules.filter((r) => r.fired).sort((a, b) => b.strength - a.strength);
    const story = fired.slice(0, 4).map((r) => sigCard(r, true)).join('') || `<p class="muted">${esc(t('nothing_fired'))}</p>`;
    const cal = D.calendar.filter((c) => c.status !== 'done').slice(0, 5).map(calItem).join('');
    const evs = D.events.slice(0, 5).map(evItem).join('') || `<p class="muted">${esc(t('no_events'))}</p>`;
    return `<div class="view">
      <div id="liveSlot">${liveSection()}</div>
      <div class="grid g-hero" style="margin-top:12px">
        <section class="card hero ${p.sufficient ? '' : 'insufficient'}">
          <div class="hero-top"><div><div class="eyebrow">${esc(t('ppi'))}</div><div class="tiny muted">${esc(t('ppi_scale'))}</div></div>
            <span class="pill" title="${esc(t('help_ppi'))}">ⓘ ${esc(fmtDate(D.as_of))}</span></div>
          <div class="gauge-wrap">${gaugeSvg(p.value)}
            <div><div class="gauge-val num verdict-${vc}">${p.value == null ? '—' : (p.value > 0 ? '+' : '') + nf(p.value, 1)}</div>
              <div class="gauge-label verdict-${vc}">${esc(vtxt)}</div>
              <div class="covbar"><span style="width:${p.coverage_pct}%"></span></div>
              <div class="tiny muted">${Math.round(p.coverage_pct)}% ${esc(t('coverage'))}${p.sufficient ? '' : ' · ' + esc(t('insufficient'))}</div></div></div>
          <div class="subs" style="margin-top:14px">${subs}<div style="height:6px"></div>${extra}</div>
        </section>
        <section class="card"><h3>${esc(t('todays_story'))}<a href="#/signals" data-route="signals" class="small">${esc(t('see_all'))} →</a></h3>
          <div class="story">${story}</div></section>
      </div>
      <h2 class="sec">${esc(t('key_numbers'))}</h2>
      <div class="grid kpis">${KPIS.map(tile).join('')}</div>
      <div class="grid g-2" style="margin-top:12px">${chartCard('fx')}${chartCard('brent')}</div>
      <div class="grid g-2" style="margin-top:12px">
        <section class="card"><h3>${esc(t('upcoming'))}<a href="#/calendar" data-route="calendar" class="small">→</a></h3><div class="cal">${cal}</div></section>
        <section class="card"><h3>${esc(t('active_events'))}<a href="#/signals" data-route="signals" class="small">→</a></h3><div class="timeline">${evs}</div></section>
      </div>
      <p class="disclaimer">${esc(t('disclaimer'))}</p></div>`;
  }
  function viewDomain(id) {
    const d = S.D.domains.find((x) => x.id === id);
    if (!d) return viewOverview();
    const rules = S.D.rules.filter((r) => RULE_DOMAIN[r.domain] === id && r.fired);
    const charts = (DOMAIN_CHARTS[id] || []).map((k) => chartCard(k)).join('');
    return `<div class="view"><div class="page-head"><div><h1>${esc(DOMAIN_ICON[id] || '')} ${esc(AR() ? d.name_ar : d.name_en)}</h1></div></div>
      ${charts ? `<div class="grid g-2">${charts}</div>` : ''}
      <h2 class="sec">${esc(t('key_numbers'))}</h2><div class="grid g-tiles">${d.series.map(tile).join('')}</div>
      <h2 class="sec">${esc(t('domain_signals'))}</h2><div class="story">${rules.map((r) => sigCard(r)).join('') || `<p class="muted">${esc(t('nothing_fired'))}</p>`}</div></div>`;
  }
  function viewSignals() {
    const f = S.sigFilter;
    const R = S.D.rules.filter((r) => f === 'all' ? true : f === 'fired' ? r.fired : f === 'pressure' ? r.fired && r.direction > 0 :
      f === 'relief' ? r.fired && r.direction < 0 : f === 'notes' ? r.fired && r.direction === 0 : f === 'ne' ? !r.evaluable : true);
    const counts = { fired: S.D.rules.filter((r) => r.fired).length, ne: S.D.rules.filter((r) => !r.evaluable).length, all: S.D.rules.length };
    const chip = (k, label, n) => `<button class="chip" data-sig="${k}" aria-pressed="${f === k}">${esc(label)}${n != null ? ` · ${n}` : ''}</button>`;
    const q = S.D.queue.map((e) => `<div class="ev"><div class="d num">${esc(e.event_date)}</div><div class="t"><a dir="auto" href="${esc(e.source_url)}" target="_blank" rel="noopener">${esc(e.title_en)}</a>
      <small>${esc(e.event_type)} · ${esc(e.source_name)}</small></div><span class="pill">${e.n_outlets} ${AR() ? 'مصدر' : 'outlet' + (e.n_outlets === 1 ? '' : 's')}</span></div>`).join('');
    return `<div class="view"><div class="page-head"><div><h1>${esc(t('signals'))}</h1><p>${esc(t('tool_default'))}</p></div></div>
      <div class="chips">${chip('fired', t('fired'), counts.fired)}${chip('pressure', t('pressure_word'))}${chip('relief', t('relief_word'))}${chip('notes', t('notes'))}${chip('ne', t('not_evaluable'), counts.ne)}${chip('all', t('all'), counts.all)}</div>
      <div class="story">${R.map((r) => sigCard(r)).join('') || `<p class="muted">${esc(t('nothing_fired'))}</p>`}</div>
      <h2 class="sec">${esc(t('events_title'))}</h2><div class="timeline">${S.D.events.map(evItem).join('') || `<p class="muted">${esc(t('no_events'))}</p>`}</div>
      <h2 class="sec">${esc(t('review_queue'))} <span class="pill">${S.D.queue.length}</span></h2><p class="small muted">${esc(t('review_hint'))}</p>
      <div class="timeline">${q || `<p class="muted">${esc(t('queue_empty'))}</p>`}</div></div>`;
  }
  function evItem(e) {
    const color = e.direction > 0 ? 'var(--pressure)' : e.direction < 0 ? 'var(--relief)' : 'var(--sand)';
    return `<div class="ev"><div class="d num">${esc(fmtDate(e.event_date))}</div>
      <div class="t"><span dir="auto">${esc(AR() ? e.title_ar || e.title_en : e.title_en)}</span><small>${esc(e.event_type)} · ${esc(e.confidence)}${e.direction === 0 ? ' · ' + esc(t('tag_only')) : ''} · <a href="${esc(e.source_url)}" target="_blank" rel="noopener">${esc(e.source_name)}</a></small></div>
      <div title="${esc(t('weight_left'))} ${Math.round(e.weight_left * 100)}%"><div class="decay"><span style="width:${Math.round(e.weight_left * 100)}%;background:${color}"></span></div>
      <div class="tiny muted num" style="text-align:end">${e.score > 0 ? '+' : ''}${nf(e.score, 2)}</div></div></div>`;
  }
  function calItem(c) {
    const when = c.event_date + 'T' + (c.event_time_cairo || '09:00') + ':00+03:00';
    const cd = until(when);
    const today = S.D.as_of;
    const dayLabel = c.event_date === today ? t('today') : fmtDate(c.event_date);
    return `<div class="cal-item"><div class="when">${esc(dayLabel)}<small class="num">${esc(c.event_time_cairo || '')}</small></div>
      <div><a dir="auto" href="${esc(c.source_url)}" target="_blank" rel="noopener">${esc(c.description)}</a> <span class="pill">${esc(c.status)}</span></div>
      ${cd ? `<span class="countdown">${esc(cd)}</span>` : '<span></span>'}</div>`;
  }
  function viewCalendar() {
    const items = S.D.calendar;
    return `<div class="view"><div class="page-head"><div><h1>${esc(t('calendar'))}</h1><p>${esc(AR() ? 'مواعيد الإصدارات والقرارات بتوقيت القاهرة. المواعيد المتكررة تقديرية.' : 'Releases and decisions in Cairo time. Recurring dates are expected patterns, not confirmed.')}</p></div></div>
      <div class="cal">${items.map(calItem).join('') || `<p class="muted">—</p>`}</div>
      <h2 class="sec">${esc(t('next_update'))}</h2><div class="cal">${S.D.next_runs.map((r) => `<div class="cal-item"><div class="when">${esc(fmtDate(r.at.slice(0, 10)))}<small class="num">${esc(r.at.slice(11, 16))}</small></div><div>pulse run --job ${esc(r.job)}</div><span class="countdown">${esc(until(r.at))}</span></div>`).join('')}</div></div>`;
  }
  function mdToHtml(md) {
    const lines = md.split('\n');
    let html = '', inUl = false, inRefs = false, inTable = false;
    const close = () => { if (inUl) { html += '</ul>'; inUl = false; } if (inTable) { html += '</table>'; inTable = false; } };
    for (const raw of lines) {
      const l = raw.trimEnd();
      if (l.startsWith('# ')) { close(); html += `<h1>${esc(l.slice(2))}</h1>`; continue; }
      if (l.startsWith('## ')) { close(); if (inRefs) { html += '</div>'; inRefs = false; } const h = l.slice(3); html += `<h2>${esc(h)}</h2>`; if (h === 'المراجع') { html += '<div class="refs">'; inRefs = true; } continue; }
      if (l.startsWith('|')) { const cells = l.replace(/^\||\|$/g, '').split('|').map((x) => x.trim()); if (cells.every((c) => /^-+$/.test(c))) continue;
        if (!inTable) { close(); html += '<table>'; inTable = true; } html += '<tr>' + cells.map((c) => `<td>${esc(c)}</td>`).join('') + '</tr>'; continue; }
      if (/^\s*- /.test(l)) { if (!inUl) { close(); html += '<ul>'; inUl = true; } const sub = /^\s{2,}- /.test(l); html += `<li${sub ? ' style="margin-inline-start:18px;list-style:circle"' : ''}>${esc(l.replace(/^\s*- /, ''))}</li>`; continue; }
      const m = l.match(/^(\d+)\. (.*) — (\S+)$/);
      if (m) { close(); const url = m[3]; html += `<div>${m[1]}. ${url.startsWith('http') ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(m[2])}</a>` : esc(m[2] + ' — ' + url)}</div>`; continue; }
      if (l.trim()) { close(); html += `<p>${esc(l)}</p>`; } else close();
    }
    close(); if (inRefs) html += '</div>';
    return html.replace(/⁦([^⁩]*)⁩/g, '<span class="num">$1</span>');
  }
  function viewBrief() {
    const b = S.D.brief;
    return `<div class="view"><div class="page-head"><div><h1>${esc(t('brief'))}</h1><p class="num">${esc(b.date)}</p></div>
      <div style="display:flex;gap:8px"><button class="btn" type="button" onclick="window.print()">⎙ ${esc(t('print'))}</button>
      <a class="btn" href="briefs/${esc(b.date)}.html" target="_blank" rel="noopener">${esc(t('open_file'))} ↗</a></div></div>
      <article class="card brief" lang="ar">${b.md ? mdToHtml(b.md) : `<p>${esc(t('no_data'))}</p>`}</article></div>`;
  }
  function viewData() {
    const c = S.D.coverage;
    const f = S.dataFilter.toLowerCase();
    const rows = Object.values(S.D.series).filter((s) => !f || (s.id + ' ' + s.name_en + ' ' + s.name_ar).toLowerCase().includes(f))
      .map((s) => `<tr><td><a href="#/s/${s.id}" data-series="${s.id}">${esc(nm(s))}</a><div class="tiny muted">${esc(s.id)}</div></td>
        <td class="num">${s.empty ? '—' : valueHtml(s)}</td><td class="num">${esc(s.date || '')}</td><td>${s.empty ? `<span class="pill">${esc(s.access)}</span>` : badges(s)}</td>
        <td class="small">${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.source)}</a>` : esc(s.source || '')}</td></tr>`).join('');
    const src = S.D.sources.map((s) => `<tr><td>${esc(s.source)}</td><td class="${s.status === 'ok' ? 'status-ok' : 'status-err'}">${s.status === 'ok' ? '● ok' : '● ' + esc(t('error'))}</td>
      <td class="num small">${esc((s.at || '').replace('T', ' ').slice(0, 16))} UTC</td><td class="num">${s.rows ?? ''}</td><td class="small muted">${esc(s.error || '')}</td></tr>`).join('');
    return `<div class="view"><div class="page-head"><div><h1>${esc(t('data'))}</h1></div></div>
      <div class="grid g-3">
        <section class="card"><h3>${esc(t('coverage_title'))}</h3><div class="gauge-val num">${c.total - c.missing}<span class="muted" style="font-size:18px"> / ${c.total}</span></div>
          <div class="covbar"><span style="width:${(c.total - c.missing) / c.total * 100}%"></span></div>
          <div class="small muted">${c.fresh} ${esc(t('fresh'))} · ${c.stale} ${esc(t('stale'))} · ${c.very_stale} ${esc(t('very_stale'))} · ${c.manual_missing} MANUAL/PAID ${esc(t('no_data'))}</div></section>
        <section class="card"><h3>${esc(t('ppi'))}</h3><div class="gauge-val num">${Math.round(S.D.ppi.coverage_pct)}%</div><div class="small muted">${esc(t('coverage'))} · min ${S.D.ppi.min_coverage_pct}%</div></section>
        <section class="card"><h3>${esc(t('updated'))}</h3><div class="gauge-val" style="font-size:22px">${esc(ago(S.D.generated))}</div><div class="small muted num">${esc(S.D.generated.replace('T', ' ').slice(0, 16))} (Cairo)</div></section>
      </div>
      <section class="card" style="margin-top:12px"><h3>${esc(t('ppi_history'))}</h3><div class="chart tall" dir="ltr" id="ch_ppihist"></div><div class="cap">${esc(t('backtest_note'))}</div></section>
      ${S.D.audit ? `<h2 class="sec">${esc(AR() ? 'مراجعة جودة البيانات' : 'Data audit (economist checks)')}
        <span class="pill">${S.D.audit.counts.pass} ✓ · ${S.D.audit.counts.warn} ! · ${S.D.audit.counts.fail} ✕</span></h2>
        <div class="card tblwrap"><table class="tbl">${S.D.audit.checks.map((c) => `<tr><td><span class="pill ${c.status === 'pass' ? '' : c.status === 'warn' ? 'warn' : 'crit'}">${c.status === 'pass' ? '✓ pass' : c.status === 'warn' ? '! watch' : '✕ fail'}</span></td>
        <td><b>${esc(c.check)}</b><div class="small muted">${esc(c.detail)}</div></td></tr>`).join('')}</table></div>` : ''}
      <h2 class="sec">${esc(t('sources_title'))}</h2><div class="card tblwrap"><table class="tbl"><tr><th>collector</th><th>${esc(t('status'))}</th><th>time</th><th>${esc(t('rows'))}</th><th>${esc(t('error'))}</th></tr>${src}</table></div>
      <h2 class="sec">${esc(t('all_series'))}</h2><input class="btn" style="width:100%;height:40px;margin-bottom:10px" id="dataFilter" placeholder="${esc(t('filter_series'))}" value="${esc(S.dataFilter)}">
      <div class="card tblwrap"><table class="tbl"><tr><th>${esc(t('all_series'))}</th><th>value</th><th>${esc(t('observed'))}</th><th>${esc(t('status'))}</th><th>${esc(t('source'))}</th></tr>${rows}</table></div></div>`;
  }
  function drawPpiHistory() {
    const el = document.getElementById('ch_ppihist');
    if (!el || !window.Plotly) return;
    const H = S.D.ppi.history;
    const bt = H.filter((r) => r.kind === 'backtest'), live = H.filter((r) => r.kind === 'live');
    const traces = [
      { type: 'scatter', mode: 'lines', name: 'backtest (weekly)', x: bt.map((r) => r.run_date), y: bt.map((r) => r.value), line: { color: css('--s1'), width: 2 },
        customdata: bt.map((r) => r.coverage_pct), hovertemplate: 'PPI %{y:.1f}<br>coverage %{customdata:.0f}%<extra></extra>' },
      { type: 'scatter', mode: 'markers', name: 'live', x: live.map((r) => r.run_date), y: live.map((r) => r.value), marker: { size: 9, color: css('--sand') },
        hovertemplate: 'PPI %{y:.1f}<extra>live</extra>' }];
    Plotly.react(el, traces, baseLayout({ shapes: [hline(0, '--muted', '')], yaxis: { range: [-100, 100], gridcolor: css('--border'), zeroline: false } }), { displayModeBar: false, responsive: true });
  }

  // ------------------------------------------------------------------ drawer (series detail)
  async function openSeries(id) {
    const s = S.D.series[id];
    if (!s) return;
    const dr = $('#drawer');
    const body = $('#drawerBody');
    const ch = changeInfo(s);
    body.innerHTML = `<h2 class="d-title" id="drawerTitle">${esc(nm(s))}</h2><p class="d-sub"><bdi>${esc(AR() ? s.name_en : s.name_ar)}</bdi> · <code>${esc(s.id)}</code></p>
      <div class="d-big"><span class="v">${s.empty ? esc(t('no_data')) : valueHtml(s)}</span>
        ${ch ? `<span class="t-chg ${ch.cls}" style="font-size:15px">${ch.arrow} <span class="num">${esc(ch.txt)}</span> ${esc(t('vs'))} <span class="num">${esc(fmtObs(s.prev_date, s.freq))}</span> ${ch.word ? '· ' + esc(ch.word) : ''}</span>` : ''}
        ${s.empty ? '' : badges(s)}</div>
      ${explainPanel(s)}
      <div class="card" style="margin-top:12px"><h3>${esc(t('history'))}<span id="dRange"></span></h3><div class="chart" dir="ltr" id="dChart"><div class="muted small">…</div></div></div>
      <div class="facts">
        <div class="fact"><b>${esc(t('source'))}</b>${s.url ? `<a dir="auto" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.source)} ↗</a>` : `<bdi>${esc(s.source || s.access)}</bdi>`}</div>
        <div class="fact"><b>${esc(t('observed'))} / ${esc(t('released'))}</b><span class="num">${esc(s.date || '—')}${s.obs_time ? ' ' + esc(s.obs_time.slice(11, 16)) : ''} / ${esc(s.release || '—')}</span></div>
        <div class="fact"><b>${esc(t('quality'))}</b>${esc(meta(s.quality || '—'))} · ${esc(meta(s.access))}</div>
        <div class="fact"><b>${esc(t('frequency'))} · ${esc(t('unit'))}</b>${esc(meta(s.freq))} · <bdi>${esc(s.unit || '—')}</bdi></div>
        ${s.definition ? `<div class="fact" style="grid-column:1/-1"><b>${esc(t('definition'))}</b><span dir="auto">${esc(s.definition)}</span></div>` : ''}
        ${s.note ? `<div class="fact" style="grid-column:1/-1"><b>${esc(AR() ? 'ملاحظة' : 'note')}</b><span dir="auto">${esc(s.note)}</span></div>` : ''}
      </div>
      <h3 style="display:flex;justify-content:space-between;align-items:center">${esc(t('latest_obs'))}<button class="btn" id="dCsv" type="button">⇩ ${esc(t('download_csv'))}</button></h3>
      <div class="tblwrap" id="dTable"></div>`;
    dr.classList.add('open'); dr.setAttribute('aria-hidden', 'false');
    $('.close', dr).focus();
    if (location.hash !== '#/s/' + id) history.replaceState(null, '', '#/s/' + id);
    try {
      const p = await loadSeries(id);
      const rows = p.rows;
      let range = rows.length > 400 ? '1Y' : 'All';
      const draw = () => {
        const start = rangeStart(range);
        const pts = rows.filter((r) => !start || r[0] >= start);
        const many = pts.length > 60;
        const tr = { type: many || s.freq === 'daily' ? 'scatter' : 'scatter', mode: many ? 'lines' : 'lines+markers', name: nm(s),
          x: pts.map((r) => r[0]), y: pts.map((r) => r[1]), line: { color: css('--s1'), width: 2, shape: ['event'].includes(s.freq) ? 'hv' : 'linear' },
          marker: { size: 7, color: css('--s1') }, hovertemplate: '%{x}<br>%{y:,.4g}<extra></extra>' };
        if (window.Plotly) Plotly.react('dChart', [tr], baseLayout({ showlegend: false }), { displayModeBar: false, responsive: true });
        $('#dRange').innerHTML = rangeBar('drawer', range);
        $$('#dRange [data-range]').forEach((b) => b.addEventListener('click', () => { range = b.dataset.range; draw(); }));
      };
      if (!rows.length) { $('#dChart').innerHTML = `<div class="empty-state">${esc(s.access === 'MANUAL' || s.access === 'PAID' ? t('manual_hint') : t('no_data'))}</div>`; }
      else draw();
      $('#dTable').innerHTML = `<table class="tbl"><tr><th>${esc(t('observed'))}</th><th>value</th><th>${esc(t('source'))}</th><th>${esc(t('quality'))}</th></tr>` +
        rows.slice(-15).reverse().map((r) => `<tr><td class="num">${esc(r[0])}</td><td class="num">${nf(r[1], digitsFor(r[1], s.unit))}</td>
          <td class="small">${r[3] ? `<a href="${esc(r[3])}" target="_blank" rel="noopener">${esc(r[2])}</a>` : esc(r[2])}</td><td class="small">${esc(r[4])}</td></tr>`).join('') + '</table>';
      $('#dCsv').onclick = () => {
        const csv = '﻿date,value,source,url,quality\n' + rows.map((r) => r.map((x) => `"${String(x ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
        const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = `${id}.csv`; a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      };
    } catch (e) { $('#dChart').innerHTML = `<div class="empty-state">${esc(e.message)}</div>`; }
  }
  function closeDrawer() {
    const dr = $('#drawer'); if (!dr.classList.contains('open')) return;
    S.tour = null;
    dr.classList.remove('open'); dr.setAttribute('aria-hidden', 'true');
    if (location.hash.startsWith('#/s/')) history.replaceState(null, '', '#/' + S.route);
  }

  // ------------------------------------------------------------------ palette (search)
  function paletteItems(q) {
    q = q.trim().toLowerCase();
    const views = [['overview', t('overview')], ['signals', t('signals')], ['calendar', t('calendar')], ['brief', t('brief')], ['data', t('data')],
      ...S.D.domains.map((d) => ['d/' + d.id, (AR() ? d.name_ar : d.name_en)])].map(([r, l]) => ({ kind: 'view', route: r, label: l, sub: '↵' }));
    const series = Object.values(S.D.series).map((s) => ({ kind: 'series', id: s.id, label: nm(s), sub: s.empty ? t('no_data') : `${s.display || ''}`, hay: `${s.id} ${s.name_en} ${s.name_ar}`.toLowerCase() }));
    const all = [...views, ...series];
    if (!q) return all.slice(0, 12);
    return all.filter((x) => (x.hay || x.label.toLowerCase()).includes(q) || x.label.toLowerCase().includes(q)).slice(0, 30);
  }
  function renderPalette() {
    const items = paletteItems($('#paletteInput').value);
    S.palIndex = Math.min(S.palIndex, Math.max(0, items.length - 1));
    $('#paletteList').innerHTML = items.map((x, i) => `<li role="option" data-i="${i}" aria-selected="${i === S.palIndex}">
      <span>${x.kind === 'view' ? '→ ' : ''}${esc(x.label)}</span><small class="num">${esc(x.sub || '')}</small></li>`).join('') || `<li>${esc(t('no_data'))}</li>`;
    $('#paletteList').onclick = (e) => { const li = e.target.closest('li[data-i]'); if (li) choosePalette(items[+li.dataset.i]); };
    $('#paletteInput').onkeydown = (e) => {
      if (e.key === 'ArrowDown') { S.palIndex = Math.min(items.length - 1, S.palIndex + 1); renderPalette(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { S.palIndex = Math.max(0, S.palIndex - 1); renderPalette(); e.preventDefault(); }
      else if (e.key === 'Enter') { choosePalette(items[S.palIndex]); }
    };
  }
  function choosePalette(x) { if (!x) return; closePalette(); if (x.kind === 'view') go(x.route); else openSeries(x.id); }
  function openPalette() { const p = $('#palette'); p.classList.add('open'); p.setAttribute('aria-hidden', 'false'); $('#paletteInput').value = ''; S.palIndex = 0;
    $('#paletteInput').placeholder = AR() ? 'دوّر في 199 مؤشر…' : 'Search 199 indicators…'; renderPalette(); $('#paletteInput').focus();
    $('#paletteInput').oninput = () => { S.palIndex = 0; renderPalette(); }; }
  function closePalette() { const p = $('#palette'); p.classList.remove('open'); p.setAttribute('aria-hidden', 'true'); }

  // ------------------------------------------------------------------ navigation
  function navItems() {
    return [['overview', '◉', t('overview')], ...S.D.domains.map((d) => ['d/' + d.id, DOMAIN_ICON[d.id], AR() ? d.name_ar : d.name_en]),
      ['signals', 'ϟ', t('signals')], ['calendar', '▦', t('calendar')], ['brief', 'ع', t('brief')], ['data', '≡', t('data')]];
  }
  function priceBar() {
    const el = $('#pricebar');
    if (!el || !S.D) return;
    const L = S.L;
    const items = [];
    const fx = L && L.cbe ? L.cbe.buy : (S.D.series.fx_cbe_official || {}).value;
    if (fx) items.push(['$', nf(fx, 2), null]);
    const gi = (S.D.series.fx_gold_implied || {}).value;
    if (gi) items.push([AR() ? 'دولار الدهب' : 'Gold $', nf(gi, 2), null]);
    for (const [id, lab, labAr, d] of [['brent', 'Oil', 'بترول', 1], ['egx30', 'EGX30', 'البورصة', 0], ['gold', 'Gold', 'دهب', 0]]) {
      const q = L ? L.quotes.find((x) => x.id === id) : null;
      if (q) items.push([AR() ? labAr : lab, (id === 'brent' ? '$' : '') + nf(q.price, id === 'egx30' || id === 'gold' ? 0 : 1), q.chg_pct, q.sign]);
    }
    el.innerHTML = items.map(([l, v, c, sg]) => {
      const cls = c == null ? '' : (Math.sign(c) * (sg || 0) > 0 ? 'p' : Math.sign(c) * (sg || 0) < 0 ? 'r' : '');
      return `<span class="pb"><span>${esc(l)}</span><b class="num">${v}</b>${c == null ? '' : `<i class="num ${cls}">${c > 0 ? '+' : ''}${nf(c, 1)}%</i>`}</span>`;
    }).join('') + `<span class="pb"><i>● ${esc(ago(L ? L.generated : S.D.generated))}</i></span>`;
  }
  function renderNav() {
    document.documentElement.dataset.ui = S.mode;
    priceBar();
    $$('[data-mode-btn]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.modeBtn === S.mode)));
    $('#explainBtn').hidden = S.mode === 'simple';
    if (S.mode === 'simple') {
      const items = [['home', '◉', t('home')], ['learn', '✎', t('learn_tab')], ['live', '●', t('live_tab')], ['brief', 'ع', t('brief')]];
      $('#tabs').innerHTML = items.map(([r, ic, l]) => `<button class="tab" type="button" data-route="${r}" ${S.route === r || (r === 'learn' && S.route.startsWith('learn')) ? 'aria-current="page"' : ''}><span aria-hidden="true">${ic}</span>${esc(l)}</button>`).join('');
      $('#bottombar').innerHTML = [...items, ['__search', '⌕', t('search')]].map(([r, ic, l]) => `<button type="button" data-route="${r}" ${S.route === r ? 'aria-current="page"' : ''}><span aria-hidden="true">${ic}</span><span>${esc(l)}</span></button>`).join('');
      return;
    }
    const fired = S.D.rules.filter((r) => r.fired && r.direction > 0).length;
    $('#tabs').innerHTML = navItems().map(([r, ic, l]) => `<button class="tab" type="button" data-route="${r}" ${S.route === r ? 'aria-current="page"' : ''}>
      <span aria-hidden="true">${ic}</span>${esc(l)}${r === 'signals' && fired ? `<span class="count">${fired}</span>` : ''}</button>`).join('');
    const bb = [['overview', '◉', t('overview')], ['signals', 'ϟ', t('signals')], ['brief', 'ع', t('brief')], ['calendar', '▦', t('calendar')], ['__search', '⌕', t('search')]];
    $('#bottombar').innerHTML = bb.map(([r, ic, l]) => `<button type="button" data-route="${r}" ${S.route === r ? 'aria-current="page"' : ''}><span aria-hidden="true">${ic}</span><span>${esc(l)}</span></button>`).join('');
    const cur = $('#tabs [aria-current="page"]');
    if (cur) { const bar = $('#tabs'); const r = cur.getBoundingClientRect(), b = bar.getBoundingClientRect();
      bar.scrollLeft += (r.left + r.width / 2) - (b.left + b.width / 2); }  // scroll only the tab strip, never the page
  }
  function go(route) { if (route === '__search') return openPalette(); location.hash = '#/' + route; }
  function routeFromHash() {
    const h = location.hash.replace(/^#\/?/, '');
    if (h.startsWith('s/') || h.startsWith('n/')) { if (!S.route) S.route = S.mode === 'simple' ? 'home' : 'overview'; return { route: S.route || 'overview', series: decodeURIComponent(h.slice(2)) }; }
    return { route: h || (S.mode === 'simple' ? 'home' : 'overview') };
  }
  function render(keepScroll = false) {
    if (!S.D) return;
    const y = window.scrollY;
    const r = S.route;
    let html;
    if (r === 'home') html = viewHome();
    else if (r === 'learn') html = viewLearn();
    else if (r.startsWith('learn/')) html = viewLesson(r.slice(6));
    else if (r === 'live') html = viewLiveSimple();
    else if (r === 'overview') html = viewOverview();
    else if (r.startsWith('d/')) html = viewDomain(r.slice(2));
    else if (r === 'signals') html = viewSignals();
    else if (r === 'calendar') html = viewCalendar();
    else if (r === 'brief') html = viewBrief();
    else if (r === 'data') html = viewData();
    else html = viewOverview();
    $('#main').innerHTML = html;
    renderNav();
    applyI18nStatic();
    requestAnimationFrame(() => { drawAllCharts(); if (r === 'data') drawPpiHistory(); });
    if (keepScroll) window.scrollTo(0, y); else window.scrollTo(0, 0);
    const df = $('#dataFilter');
    if (df) df.addEventListener('input', () => { S.dataFilter = df.value; const pos = df.selectionStart; render(true); const n = $('#dataFilter'); n.focus(); n.setSelectionRange(pos, pos); });
  }
  function onHash() {
    const { route, series } = routeFromHash();
    if (route.startsWith('learn/') && (!S.lesson || S.lesson.id !== route.slice(6))) S.lesson = null;
    if (route !== S.route || !$('#main .view')) { S.route = route; render(); }
    if (series) openSeries(series); else closeDrawer();
  }

  // ------------------------------------------------------------------ chrome: language, theme, live status
  function applyI18nStatic() {
    $$('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$('.seg [data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === S.lang)));
    $$('[data-mode-btn]').forEach((b) => { b.textContent = t(b.dataset.modeBtn); b.setAttribute('aria-pressed', String(b.dataset.modeBtn === S.mode)); });
    const icons = { auto: '◐', light: '☀', dark: '☾' };
    $('#themeBtn').textContent = icons[S.theme] || '◐';
    $('#themeBtn').title = `theme: ${S.theme}`;
    $('#explainBtn').setAttribute('aria-pressed', String(S.explain));
    updateLive();
    paintViewBtn();
  }
  function setMode(m) {
    S.mode = m === 'pro' ? 'pro' : 'simple'; store('pulse.mode', S.mode);
    S.tour = null; closeDrawer();
    location.hash = '#/' + (S.mode === 'simple' ? 'home' : 'overview');
    render();
  }
  function viewState() {
    const d = document.documentElement;
    return { pref: d.dataset.viewPref || 'auto', eff: d.dataset.view || 'desktop', phone: d.dataset.device === 'phone' };
  }
  function paintViewBtn() {
    const v = viewState();
    const icon = v.eff === 'mobile' ? '📱' : '🖥';
    const label = v.pref === 'auto' ? `${t('lay_auto')} (${t(v.eff === 'mobile' ? 'lay_mobile' : 'lay_desktop')})` : t(v.pref === 'mobile' ? 'lay_mobile' : 'lay_desktop');
    $('#viewBtn').innerHTML = `<span aria-hidden="true">${icon}</span>${v.pref === 'auto' ? '<small class="auto-badge">A</small>' : ''}`;
    $('#viewBtn').title = `${t('layout')}: ${label} — ${t('lay_hint')}`;
    $('#viewBtn').setAttribute('aria-label', `${t('layout')}: ${label}`);
  }
  function cycleView() {
    const order = ['auto', 'mobile', 'desktop'];
    const v = viewState();
    const pref = order[(order.indexOf(v.pref) + 1) % order.length];
    store('pulse.view', pref);
    const eff = pref === 'auto' ? (v.phone ? 'mobile' : 'desktop') : pref;
    const d = document.documentElement;
    d.dataset.viewPref = pref; d.dataset.view = eff;
    $('#vp').setAttribute('content', eff === 'desktop' && v.phone ? 'width=1280' : 'width=device-width, initial-scale=1, viewport-fit=cover');
    paintViewBtn(); render(true);
    toast(`${t('layout')}: ${pref === 'auto' ? t('lay_auto') + ' — ' : ''}${t(eff === 'mobile' ? 'lay_mobile' : 'lay_desktop')}`, '', 2500);
    setTimeout(drawAllCharts, 60);
  }
  function setLang(l) {
    S.lang = l; store('pulse.lang', l);
    document.documentElement.lang = l; document.documentElement.dir = l === 'ar' ? 'rtl' : 'ltr';
    render(true);
  }
  function cycleTheme() {
    S.theme = { auto: 'light', light: 'dark', dark: 'auto' }[S.theme] || 'auto';
    store('pulse.theme', S.theme);
    if (S.theme === 'auto') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = S.theme;
    applyI18nStatic(); setTimeout(drawAllCharts, 30); if (S.route === 'data') setTimeout(drawPpiHistory, 30);
  }
  function updateLive() {
    if (!S.D) return;
    const el = $('#live');
    const ok = S.lastPoll && Date.now() - S.lastPoll < 3 * 60 * 1000;
    el.classList.toggle('on', !!ok && !S.running);
    el.classList.toggle('busy', S.running);
    const next = S.D.next_runs && S.D.next_runs[0];
    const fresh = S.L && S.L.generated > S.D.generated ? S.L.generated : S.D.generated;
    $('#liveText').textContent = S.running ? t('running') : `${ok ? t('live') : t('snapshot')} · ${t('updated')} ${ago(fresh)}`;
    el.title = next ? `${t('next_update')}: ${next.job} ${next.at.slice(0, 16).replace('T', ' ')} (${until(next.at)})` : '';
  }
  function toast(title, body, ms = 6000) {
    const d = document.createElement('div');
    d.className = 'toast';
    d.innerHTML = `<div><b>${esc(title)}</b>${body ? esc(body) : ''}</div><button class="x" aria-label="close">✕</button>`;
    $('.x', d).onclick = () => d.remove();
    $('#toasts').appendChild(d);
    if (ms) setTimeout(() => d.remove(), ms);
  }

  // ------------------------------------------------------------------ live updates
  async function poll() {
    try {
      const m = await loadManifest();
      S.lastPoll = Date.now();
      if (m.version !== S.version) await refresh(true);
    } catch (e) { /* offline or file missing — keep the snapshot */ }
    updateLive();
  }
  async function refresh(announce) {
    const old = S.D;
    const D = await loadBundle();
    S.D = D; S.version = D.version; S.seriesCache = {};
    if (announce && old) {
      const changed = Object.keys(D.series).filter((id) => {
        const a = old.series[id], b = D.series[id];
        return a && b && (a.value !== b.value || a.date !== b.date);
      });
      S.flashIds = new Set(changed);
      toast(t('new_data'), ` — ${changed.length} ${t('changed')}. PPI ${D.ppi.value > 0 ? '+' : ''}${D.ppi.value}`);
      render(true);
      setTimeout(() => { S.flashIds = new Set(); }, 2500);
    }
  }
  async function detectServer() {
    if (!location.protocol.startsWith('http')) return;
    try {
      const r = await fetch('/api/status', { cache: 'no-store' });
      if (!r.ok) return;
      const j = await r.json();
      S.server = true; S.running = !!j.running;
      $('#runBtn').hidden = false;
    } catch (e) { /* static hosting */ }
  }
  async function runNow() {
    if (!S.server || S.running) return;
    const r = await fetch('/api/run?job=daily', { method: 'POST' });
    if (!r.ok) { toast(t('run_failed'), ''); return; }
    S.running = true; updateLive(); toast(t('running'), ' ' + t('run_started'));
    const iv = setInterval(async () => {
      try {
        const j = await (await fetch('/api/status', { cache: 'no-store' })).json();
        if (!j.running) {
          clearInterval(iv); S.running = false;
          if (j.last_exit === 0) toast(t('run_done'), '', 4000); else toast(t('run_failed'), '');
          await poll();
        }
      } catch (e) { /* keep waiting */ }
    }, 4000);
  }

  // ------------------------------------------------------------------ events
  function bind() {
    document.addEventListener('click', (e) => {
      const mb = e.target.closest('[data-more]');
      if (mb) { const c = mb.closest('.live-card'); if (c) c.classList.add('expanded'); return; }
      const nEl = e.target.closest('[data-node]');
      if (nEl) { e.preventDefault(); if (S.tour && !e.target.closest('.tourbar')) S.tour = null; openNode(nEl.dataset.node); return; }
      const tr = e.target.closest('[data-tour]');
      if (tr) { e.preventDefault(); const a = tr.dataset.tour;
        if (a === 'start') tourGo(0); else if (a === 'next') tourGo(S.tour.i + 1); else if (a === 'back') tourGo(S.tour.i - 1); else { S.tour = null; closeDrawer(); }
        return; }
      const ls = e.target.closest('[data-lstep]');
      if (ls && S.lesson) { S.lesson.i += ls.dataset.lstep === 'next' ? 1 : -1; S.lesson.i = Math.max(0, S.lesson.i); render(true); return; }
      const qz = e.target.closest('[data-quiz]');
      if (qz && S.lesson) { S.lesson.picked = +qz.dataset.quiz; S.lessonsDone.add(S.lesson.id); store('pulse.lessons', [...S.lessonsDone].join(',')); render(true); return; }
      const md = e.target.closest('[data-mode], [data-mode-btn]');
      if (md) { e.preventDefault(); setMode(md.dataset.mode || md.dataset.modeBtn); return; }
      const tEl = e.target.closest('[data-series]');
      if (tEl) { e.preventDefault(); location.hash = '#/s/' + tEl.dataset.series; return; }
      const r = e.target.closest('[data-route]');
      if (r) { e.preventDefault(); go(r.dataset.route); return; }
      const rg = e.target.closest('[data-range][data-chart]');
      if (rg && rg.dataset.chart !== 'drawer') { S.ranges[rg.dataset.chart] = rg.dataset.range; $$(`[data-chart="${rg.dataset.chart}"]`).forEach((b) => b.setAttribute('aria-pressed', String(b === rg))); drawChart(rg.dataset.chart); return; }
      const sg = e.target.closest('[data-sig]');
      if (sg) { S.sigFilter = sg.dataset.sig; render(true); return; }
      if (e.target.closest('[data-close]')) { if (e.target.closest('#palette')) closePalette(); else closeDrawer(); }
    });
    $$('.seg [data-lang]').forEach((b) => b.addEventListener('click', () => setLang(b.dataset.lang)));
    $('#themeBtn').addEventListener('click', cycleTheme);
    $('#viewBtn').addEventListener('click', cycleView);
    $('#explainBtn').addEventListener('click', () => { S.explain = !S.explain; store('pulse.explain', S.explain ? '1' : '0'); render(true); });
    $('#searchBtn').addEventListener('click', openPalette);
    $('#runBtn').addEventListener('click', runNow);
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPalette(); }
      else if (e.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); openPalette(); }
      else if (e.key === 'Escape') { closePalette(); closeDrawer(); }
    });
    window.addEventListener('hashchange', onHash);
    let y0 = null;
    const panel = $('#drawer .drawer-panel');
    panel.addEventListener('touchstart', (e) => { y0 = panel.scrollTop <= 0 ? e.touches[0].clientY : null; }, { passive: true });
    panel.addEventListener('touchend', (e) => {
      if (y0 != null && document.documentElement.dataset.view === 'mobile' && e.changedTouches[0].clientY - y0 > 90) closeDrawer();
      y0 = null;
    }, { passive: true });
    if (window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (S.theme === 'auto') setTimeout(drawAllCharts, 30); });
  }

  // ------------------------------------------------------------------ boot
  async function boot() {
    bind();
    try {
      await refresh(false);
    } catch (e) {
      $('#main').innerHTML = `<div class="empty-state"><b>No data yet.</b><br>Run <code>.venv\\Scripts\\pulse run --job all</code> then reload.</div>`;
      return;
    }
    S.lastPoll = Date.now();
    const { route, series } = routeFromHash();
    S.route = route; render();
    if (series) openSeries(series);
    await detectServer();
    updateLive();
    await pollLive(false);
    { const el = $('#liveSlot'); if (el) el.innerHTML = liveSection(); }
    setInterval(poll, 60 * 1000);
    setInterval(() => pollLive(true), 60 * 1000);
    setInterval(updateLive, 30 * 1000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) { poll(); pollLive(true); } });
    window.addEventListener('load', () => drawAllCharts());
  }
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
