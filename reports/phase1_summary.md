# Phase 1 — Core collectors

Autonomous build, 2026-10-18 (Cairo). Checkpoint not paused per build instructions.

- Collectors: `cbe_fx` (official buy/sell, history since Jan 2023: 916 days), `cbe_rates` (corridor + discount, effective 15 Feb 2026), `cbe_cpi`, `cbe_news` (NIR since Dec 2014, CPI headline/core m/m & y/y since 2023, MPC decisions since Nov 2023, GDP from MPC text), `yahoo` (5y), `gold_eg` (banklive, iSagha fallback), `pmi` (S&P PDFs: Egypt, Saudi, UAE), `fred` (2016→).
- Day-one state reproduced from primary sources: ODR 19.00 / OLR 20.00 / main op 19.50 / discount 19.50; urban CPI 13.9%, core 14.1% (Sep); NIR $57,348.2mn; USD/EGP 53.4717 buy (18 Oct); PMI 47.2 (Sep), 49.6 (Aug).
- Brent: FRED spot 126.55 (14 Oct) vs futures 109.9 (16 Oct) — a large spot–futures gap; both stored separately, not blended.
- Dashboard v0 tiles built (now ~70 tiles across 11 domains).
