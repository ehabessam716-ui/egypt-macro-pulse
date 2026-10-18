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
    help_ppi: ['Each sub-index compares today with the last 3 years (z-score → −100…+100), adds fired rules and decaying events. Weights: config/indices.yaml.',
      'كل مؤشر فرعي بيقارن النهارده بآخر 3 سنين، وبيضيف الإشارات والأحداث. الأوزان في ملف الإعدادات.'],
  };
  const DOMAIN_ICON = { fx: '£', monetary: '%', external: '⇄', fiscal: '§', energy: '◆', real: '↗', global: '◎', geo: '⌖', health: '✚' };
  const SUB_TO_DOMAIN = { external: 'external', monetary: 'monetary', fiscal: 'fiscal', commodities: 'energy', geopolitical: 'geo', global: 'global' };
  const DOMAIN_CHARTS = { fx: ['fx'], monetary: ['cpi', 'real'], external: ['nir', 'remit', 'choke'], fiscal: [], energy: ['brent'],
    real: ['pmi'], global: [], geo: ['gpr', 'choke'], health: [] };
  const RULE_DOMAIN = { fx: 'fx', monetary: 'monetary', external: 'external', fiscal: 'fiscal', energy: 'energy', real: 'real',
    gold: 'energy', global: 'global', geopolitical: 'geo', healthcare: 'health' };
  const KPIS = ['fx_cbe_official', 'gold_gap_pct', 'nir', 'cpi_urban_yoy', 'cbe_odr', 'brent', 'egx30', 'pmi'];

  // ------------------------------------------------------------------ state
  const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  const S = {
    D: null, version: null, lang: store('pulse.lang') === 'ar' ? 'ar' : 'en', theme: store('pulse.theme') || 'auto',
    route: 'overview', sigFilter: 'fired', ranges: {}, seriesCache: {}, server: false, running: false, lastPoll: null,
    palIndex: 0, flashIds: new Set(), dataFilter: '', explain: store('pulse.explain') === '1',
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
  function valueHtml(s) {
    if (s.value == null) return esc(t('no_data'));
    const u = s.unit;
    const d = digitsFor(s.value, u);
    if (u === '%') return `<span class="num">${nf(s.value, d)}%</span>`;
    if (u === 'pp') return `<span class="num">${s.value > 0 ? '+' : ''}${nf(s.value, 1)}</span><small>pp</small>`;
    const us = unitShort(u);
    return `<span class="num">${nf(s.value, d)}</span>${us ? `<small>${esc(us)}</small>` : ''}`;
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
    if (s.quality) out.push(`<span class="pill ${s.quality === 'official' ? '' : 'sand'}">${esc(s.quality)}</span>`);
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
      ${ch ? `<span class="t-chg ${ch.cls}" title="${esc(ch.word)}"><span aria-hidden="true">${ch.arrow}</span><span class="num">${esc(ch.txt)}</span></span>` : '<span class="t-chg n">&nbsp;</span>'}
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
    return `<article class="sig ${cls}">
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

  // ------------------------------------------------------------------ views
  function viewOverview() {
    const D = S.D;
    const p = D.ppi;
    const [vc, vtxt] = verdict(p.value);
    const subs = D.subindices.map((s) => `<button class="sub" data-route="d/${SUB_TO_DOMAIN[s.id]}" title="${esc(t('coverage'))} ${s.coverage_pct}%">
        <span class="nm">${esc(AR() ? s.name_ar : s.name_en)}<small class="num">${s.weight}%</small></span>${dbar(s.value)}
        <span class="val num">${s.value == null ? '—' : (s.value > 0 ? '+' : '') + Math.round(s.value)}<small>${Math.round(s.coverage_pct)}%</small></span></button>`).join('');
    const extra = D.extra.map((x) => `<div class="sub" style="cursor:default"><span class="nm">${esc(t(x.id === 'inflation' ? 'inflation_idx' : 'growth_idx'))}</span>
        ${dbar(x.value, '--s2', '--s3')}<span class="val num">${x.value == null ? '—' : (x.value > 0 ? '+' : '') + Math.round(x.value)}<small>${Math.round(x.coverage_pct)}%</small></span></div>`).join('');
    const fired = D.rules.filter((r) => r.fired).sort((a, b) => b.strength - a.strength);
    const story = fired.slice(0, 4).map((r) => sigCard(r, true)).join('') || `<p class="muted">${esc(t('nothing_fired'))}</p>`;
    const cal = D.calendar.filter((c) => c.status !== 'done').slice(0, 5).map(calItem).join('');
    const evs = D.events.slice(0, 5).map(evItem).join('') || `<p class="muted">${esc(t('no_events'))}</p>`;
    return `<div class="view">
      <div class="grid g-hero">
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
    const q = S.D.queue.map((e) => `<div class="ev"><div class="d num">${esc(e.event_date)}</div><div class="t"><a href="${esc(e.source_url)}" target="_blank" rel="noopener">${esc(e.title_en)}</a>
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
      <div class="t">${esc(AR() ? e.title_ar || e.title_en : e.title_en)}<small>${esc(e.event_type)} · ${esc(e.confidence)}${e.direction === 0 ? ' · ' + esc(t('tag_only')) : ''} · <a href="${esc(e.source_url)}" target="_blank" rel="noopener">${esc(e.source_name)}</a></small></div>
      <div title="${esc(t('weight_left'))} ${Math.round(e.weight_left * 100)}%"><div class="decay"><span style="width:${Math.round(e.weight_left * 100)}%;background:${color}"></span></div>
      <div class="tiny muted num" style="text-align:end">${e.score > 0 ? '+' : ''}${nf(e.score, 2)}</div></div></div>`;
  }
  function calItem(c) {
    const when = c.event_date + 'T' + (c.event_time_cairo || '09:00') + ':00+03:00';
    const cd = until(when);
    const today = S.D.as_of;
    const dayLabel = c.event_date === today ? t('today') : fmtDate(c.event_date);
    return `<div class="cal-item"><div class="when">${esc(dayLabel)}<small class="num">${esc(c.event_time_cairo || '')}</small></div>
      <div><a href="${esc(c.source_url)}" target="_blank" rel="noopener">${esc(c.description)}</a> <span class="pill">${esc(c.status)}</span></div>
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
    body.innerHTML = `<h2 class="d-title" id="drawerTitle">${esc(nm(s))}</h2><p class="d-sub">${esc(AR() ? s.name_en : s.name_ar)} · <code>${esc(s.id)}</code></p>
      <div class="d-big"><span class="v">${s.empty ? esc(t('no_data')) : valueHtml(s)}</span>
        ${ch ? `<span class="t-chg ${ch.cls}" style="font-size:15px">${ch.arrow} <span class="num">${esc(ch.txt)}</span> ${esc(t('vs'))} <span class="num">${esc(fmtObs(s.prev_date, s.freq))}</span> ${ch.word ? '· ' + esc(ch.word) : ''}</span>` : ''}
        ${s.empty ? '' : badges(s)}</div>
      ${explainPanel(s)}
      <div class="card" style="margin-top:12px"><h3>${esc(t('history'))}<span id="dRange"></span></h3><div class="chart" dir="ltr" id="dChart"><div class="muted small">…</div></div></div>
      <div class="facts">
        <div class="fact"><b>${esc(t('source'))}</b>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.source)} ↗</a>` : esc(s.source || s.access)}</div>
        <div class="fact"><b>${esc(t('observed'))} / ${esc(t('released'))}</b><span class="num">${esc(s.date || '—')}${s.obs_time ? ' ' + esc(s.obs_time.slice(11, 16)) : ''} / ${esc(s.release || '—')}</span></div>
        <div class="fact"><b>${esc(t('quality'))}</b>${esc(s.quality || '—')} · ${esc(s.access)}</div>
        <div class="fact"><b>${esc(t('frequency'))} · ${esc(t('unit'))}</b>${esc(s.freq)} · ${esc(s.unit || '—')}</div>
        ${s.definition ? `<div class="fact" style="grid-column:1/-1"><b>${esc(t('definition'))}</b>${esc(s.definition)}</div>` : ''}
        ${s.note ? `<div class="fact" style="grid-column:1/-1"><b>note</b>${esc(s.note)}</div>` : ''}
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
  function renderNav() {
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
    if (h.startsWith('s/')) { if (!S.route) S.route = 'overview'; return { route: S.route || 'overview', series: decodeURIComponent(h.slice(2)) }; }
    return { route: h || 'overview' };
  }
  function render(keepScroll = false) {
    if (!S.D) return;
    const y = window.scrollY;
    const r = S.route;
    let html;
    if (r === 'overview') html = viewOverview();
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
    if (route !== S.route || !$('#main .view')) { S.route = route; render(); }
    if (series) openSeries(series); else closeDrawer();
  }

  // ------------------------------------------------------------------ chrome: language, theme, live status
  function applyI18nStatic() {
    $$('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$('.seg [data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === S.lang)));
    const icons = { auto: '◐', light: '☀', dark: '☾' };
    $('#themeBtn').textContent = icons[S.theme] || '◐';
    $('#themeBtn').title = `theme: ${S.theme}`;
    $('#explainBtn').setAttribute('aria-pressed', String(S.explain));
    updateLive();
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
    $('#liveText').textContent = S.running ? t('running') : `${ok ? t('live') : t('snapshot')} · ${t('updated')} ${ago(S.D.generated)}`;
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
    $('#explainBtn').addEventListener('click', () => { S.explain = !S.explain; store('pulse.explain', S.explain ? '1' : '0'); render(true); });
    $('#searchBtn').addEventListener('click', openPalette);
    $('#runBtn').addEventListener('click', runNow);
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPalette(); }
      else if (e.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); openPalette(); }
      else if (e.key === 'Escape') { closePalette(); closeDrawer(); }
    });
    window.addEventListener('hashchange', onHash);
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
    setInterval(poll, 60 * 1000);
    setInterval(updateLive, 30 * 1000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
    window.addEventListener('load', () => drawAllCharts());
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
