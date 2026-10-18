# Data audit — 2026-10-19

9 pass · 2 to watch · 0 fail

| status | check | detail |
|---|---|---|
| PASS | Plausible ranges (32 series) | all values inside expected ranges |
| PASS | CPI identity yearly vs monthly (26 months testable) | every testable month is consistent (rounding ±0.4pp) |
| PASS | Interest-rate corridor deposit ≤ main ≤ lending | 25 MPC observations in order |
| PASS | BoP: trade balance = oil + non-oil | consistent (within rounding) |
| PASS | Reserves = FX + gold + SDR | consistent |
| PASS | Dollar rate: official vs market vs gold-implied | market +0.05%, gold-implied +0.07% vs official 53.4717 (2026-10-18) |
| WARN | Brent: dated spot vs benchmark futures | spot premium +19.3% on 2026-10-14 — the budget comparison uses benchmark futures; a wide premium signals a physical supply squeeze (or a source issue worth watching) |
| PASS | CIB London-implied rate vs official | latest +3.1% vs 60-session average +3.3% (structural gap ~15% in 2024–25 from GDR conversion limits; read the change) |
| PASS | One-day jumps beyond normal | only known events (e.g. the March 2024 float) |
| WARN | Automatic sources fresh | very stale / empty: gdelt_red_sea_tone (no data), gdelt_hormuz_tone (no data), gdelt_iran_war_tone (no data), gdelt_gaza_tone (no data) |
| PASS | Spec seeds vs primary sources | no conflicts |

## Fixes made from earlier audits

- CPI m/m: the CBE writes negatives in words ('negative 0.5 percent'); the parser dropped the word, so 4 deflation
  months were stored as positive (May 2024, Jun 2025, Jul 2025, Jun 2026). Fixed + re-parsed + unit test.
- Brent: dated spot (EIA) ran 19–25% above benchmark futures in Oct 2026. The daily oil-vs-budget signal used spot while
  the live layer used futures. Both now use benchmark futures; the spot premium is tracked as its own indicator.
