# Data audit — 2026-10-19

7 pass · 1 to watch · 0 fail

| status | check | detail |
|---|---|---|
| PASS | Plausible ranges (32 series) | all values inside expected ranges |
| PASS | CPI identity yearly vs monthly (0 months testable) | every testable month is consistent (rounding ±0.4pp) |
| PASS | Interest-rate corridor deposit ≤ main ≤ lending | 0 MPC observations in order |
| PASS | BoP: trade balance = oil + non-oil | consistent (within rounding) |
| PASS | Reserves = FX + gold + SDR | consistent |
| PASS | One-day jumps beyond normal | only known events (e.g. the March 2024 float) |
| WARN | Automatic sources fresh | very stale / empty: fx_cbe_official_sell (no data), fx_market (no data), egx30 (no data), cib_local (no data), cib_gdr (no data), efg_hermes (no data), tmg_stock (no data), etel_stock (no data), tbill_3m_yield (no data), tbill_6m_yield (no data), tbill_9m_yield (no data), tbill_12m_yield (no data), tbill_3m_btc (no data), tbill_6m_btc (no data), tbill_9m_btc (no data), tbill_12m_btc (no data), tbill_3m_accepted_ratio (no data), tbill_6m_accepted_ratio (no data), tbill_9m_accepted_ratio (no data), tbill_12m_accepted_ratio (no data), cbe_odr (no data), cbe_olr (no data), cbe_mainop (no data), cbe_discount (no data), cbe_mpc_decision (no data), cbe_mpc_tone (no data), interbank_overnight (no data), nir (no data), cpi_urban_yoy (no data), cpi_urban_mom (no data), cpi_core_yoy (no data), cpi_core_mom (no data), cpi_regulated_yoy (no data), cpi_regulated_mom (no data), cpi_fv_yoy (no data), cpi_fv_mom (no data), remittances (no data), remittances_yoy (no data), remittances_ytd (no data), remittances_fy (no data), bop_ca_fy (no data), bop_overall_fy (no data), capital_financial_net_fy (no data), trade_balance_fy (no data), trade_nonoil_balance_fy (no data), trade_oil_balance_fy (no data), imports_nonoil_fy (no data), imports_oil_fy (no data), exports_nonoil_fy (no data), exports_oil_fy (no data), invest_income_balance_fy (no data), services_surplus_fy (no data), tourism_receipts_fy (no data), suez_receipts_fy (no data), fdi_net_fy (no data), portfolio_net_fy (no data), suez_transits (no data), suez_capacity (no data), babelmandeb_transits (no data), babelmandeb_capacity (no data), hormuz_transits (no data), hormuz_capacity (no data), imf_weo_gdp (no data), imf_weo_cpi (no data), imf_weo_ca (no data), imf_weo_debt (no data), wb_gdp_growth (no data), pmi (no data), saudi_pmi (no data), uae_pmi (no data), gdp_growth (no data), gdp_growth_fy (no data), brent (no data), brent_fut (no data), wti (no data), wti_fut (no data), henry_hub (no data), ttf (no data), ttf_fut (no data), wheat (no data), wheat_monthly (no data), xauusd (no data), xauusd_spot (no data), xagusd (no data), gold_eg_21k (no data), gold_eg_24k (no data), gold_eg_pound (no data), fed_funds (no data), us_cpi (no data), us_core_cpi (no data), us_nfp (no data), us_unemp (no data), us10y (no data), us2y (no data), breakeven10y (no data), usd_broad (no data), dxy (no data), vix (no data), em_spread_proxy (no data), msci_em_proxy (no data), eurusd (no data), euro_area_hicp (no data), gpr_global (no data), gpr_threats (no data), gpr_acts (no data), gpr_egypt (no data), gpr_israel (no data), gpr_saudi (no data), gpr_daily (no data), gpr_daily_acts (no data), gpr_daily_threats (no data), gdelt_egypt_economy_tone (no data), gdelt_egypt_economy_vol (no data), gdelt_egyptian_pound_tone (no data), gdelt_suez_canal_tone (no data), gdelt_red_sea_tone (no data), gdelt_hormuz_tone (no data), gdelt_iran_war_tone (no data), gdelt_gaza_tone (no data) |
| PASS | Spec seeds vs primary sources | no conflicts |

## Fixes made from earlier audits

- CPI m/m: the CBE writes negatives in words ('negative 0.5 percent'); the parser dropped the word, so 4 deflation
  months were stored as positive (May 2024, Jun 2025, Jul 2025, Jun 2026). Fixed + re-parsed + unit test.
- Brent: dated spot (EIA) ran 19–25% above benchmark futures in Oct 2026. The daily oil-vs-budget signal used spot while
  the live layer used futures. Both now use benchmark futures; the spot premium is tracked as its own indicator.
