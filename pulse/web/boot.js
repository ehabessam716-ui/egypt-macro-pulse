/* Pulse — runs before first paint: language, theme, layout (phone/desktop). */
(() => {
  // apply saved theme/lang before paint (no flash)
  try {
    const q = new URLSearchParams(location.search);
    if (q.get('lang')) localStorage.setItem('pulse.lang', q.get('lang') === 'ar' ? 'ar' : 'en');
    if (q.get('theme')) localStorage.setItem('pulse.theme', q.get('theme'));
    if (q.get('mode')) localStorage.setItem('pulse.mode', q.get('mode') === 'pro' ? 'pro' : 'simple');
    if (q.get('explain')) localStorage.setItem('pulse.explain', q.get('explain') === '1' ? '1' : '0');
    if (q.get('view')) localStorage.setItem('pulse.view', q.get('view'));
    // layout: auto-detect phone vs computer, unless the reader picked one
    const pv = localStorage.getItem('pulse.view') || 'auto';
    const phone = /Android|iPhone|iPod|Mobile/i.test(navigator.userAgent) ||
      (matchMedia('(pointer: coarse)').matches && Math.min(screen.width, screen.height) < 820);
    const eff = pv === 'auto' ? (phone ? 'mobile' : 'desktop') : pv;
    document.documentElement.dataset.view = eff; document.documentElement.dataset.viewPref = pv;
    document.documentElement.dataset.device = phone ? 'phone' : 'computer';
    if (eff === 'desktop' && phone) document.getElementById('vp').setAttribute('content', 'width=1280');
    const t = localStorage.getItem('pulse.theme'); if (t && t !== 'auto') document.documentElement.dataset.theme = t;
    const l = localStorage.getItem('pulse.lang'); if (l === 'ar') { document.documentElement.lang = 'ar'; document.documentElement.dir = 'rtl'; }
  } catch (e) {}
})();
