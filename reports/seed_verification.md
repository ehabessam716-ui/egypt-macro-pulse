# Seed verification — spec seeds vs primary sources

Seeds stay in the DB as quality 'secondary'; when a primary value exists for the same date it wins.  Summary: {'confirmed': 18, 'differs': 0, 'secondary only': 30}.

| series | obs date | seed | seed source | primary value | primary source | status |
|---|---|---|---|---|---|---|
| cbe_odr | 2026-02-15 | 19.0 | Wikipedia — Central Bank of Egypt | 19.0 | Central Bank of Egypt — key CBE rates | **confirmed** |
| cbe_olr | 2026-02-15 | 20.0 | Wikipedia — Central Bank of Egypt | 20.0 | Central Bank of Egypt — key CBE rates | **confirmed** |
| cbe_mainop | 2026-02-15 | 19.5 | Wikipedia — Central Bank of Egypt | 19.5 | Central Bank of Egypt — key CBE rates | **confirmed** |
| cbe_discount | 2026-02-15 | 19.5 | CBE Monetary Policy Report Q4 2025 | 19.5 | Central Bank of Egypt — key CBE rates | **confirmed** |
| nir | 2026-09-01 | 57348.2 | Zawya/Reuters via TradingView | 57348.2 | Central Bank of Egypt — NIR press release | **confirmed** |
| nir_gold | 2026-09-01 | 17456 | Zawya/Reuters via TradingView | — | — | **secondary only** |
| nir_fx | 2026-09-01 | 39292 | Zawya/Reuters via TradingView | — | — | **secondary only** |
| nir_sdr | 2026-09-01 | 602 | Zawya/Reuters via TradingView | — | — | **secondary only** |
| cpi_urban_yoy | 2026-09-01 | 13.9 | Daily News Egypt | 13.9 | Central Bank of Egypt — CPI press release | **confirmed** |
| cpi_urban_mom | 2026-09-01 | 1.3 | EnterpriseAM | 1.3 | Central Bank of Egypt — CPI press release | **confirmed** |
| cpi_core_yoy | 2026-09-01 | 14.1 | EnterpriseAM | 14.1 | Central Bank of Egypt — CPI press release | **confirmed** |
| cpi_national_yoy | 2026-09-01 | 12.8 | Amwal Al Ghad (CAPMAS) | — | — | **secondary only** |
| cpi_health_yoy | 2026-09-01 | 5.2 | Amwal Al Ghad (CAPMAS) | — | — | **secondary only** |
| cpi_med_products_yoy | 2026-09-01 | -1.3 | Amwal Al Ghad (CAPMAS) | — | — | **secondary only** |
| infl_expectations | 2026-10-11 | 16.6 | EnterpriseAM | — | — | **secondary only** |
| infl_target | 2026-10-18 | 7.0 | Central Bank of Egypt (homepage) | — | — | **secondary only** |
| remittances_fy | 2025-07-01 | 47.3 | Manassa | 47.3 | Central Bank of Egypt — BoP press release | **confirmed** |
| bop_ca_fy | 2025-07-01 | -22.5 | Rio Times | -22.5 | Central Bank of Egypt — BoP press release | **confirmed** |
| bop_ca_fy | 2024-07-01 | -15.4 | Rio Times | -15.4 | Central Bank of Egypt — BoP press release | **confirmed** |
| imports_nonoil_fy | 2025-07-01 | 83.9 | Manassa | 83.9 | Central Bank of Egypt — BoP press release | **confirmed** |
| imports_oil_fy | 2025-07-01 | 24.9 | Manassa | 24.9 | Central Bank of Egypt — BoP press release | **confirmed** |
| remittances_ytd | 2026-08-01 | 33.9 | The New Arab | 33.9 | Central Bank of Egypt — remittances press release | **confirmed** |
| suez_revenue_fy | 2025-07-01 | 4.67 | Ahram Online (SCA chairman) | — | — | **secondary only** |
| suez_revenue_fy | 2022-07-01 | 9.4 | Ahram Online (SCA chairman) | — | — | **secondary only** |
| tourism_arrivals_ytd | 2026-08-01 | 12.7 | Egypt Independent (IDSC) | — | — | **secondary only** |
| tourism_receipts_ytd | 2026-08-01 | 12.0 | Egypt Independent (IDSC) | — | — | **secondary only** |
| ext_debt_stock | 2026-01-01 | 164.8 | Ahram Online (CBE) | — | — | **secondary only** |
| ext_debt_gdp | 2026-01-01 | 38.9 | Ahram Online (CBE) | — | — | **secondary only** |
| ext_debt_service_actual | 2025-07-01 | 28.3 | Ahram Online (CBE) | — | — | **secondary only** |
| ext_debt_service_sched | 2026-01-01 | 34.6 | The Edge (citing CBE) | — | — | **secondary only** |
| ext_debt_service_sched | 2027-01-01 | 19.6 | The Edge (citing CBE) | — | — | **secondary only** |
| ext_debt_service_sched | 2028-01-01 | 14.6 | The Edge (citing CBE) | — | — | **secondary only** |
| budget_oil_assumption | 2026-07-01 | 75 | SEE News | — | — | **secondary only** |
| pmi | 2026-09-01 | 47.2 | Trading Economics | 47.2 | S&P Global — S&P Global Egypt PMI | **confirmed** |
| pmi | 2026-08-01 | 49.6 | Trading Economics | 49.6 | S&P Global — S&P Global Egypt PMI | **confirmed** |
| pmi | 2026-07-01 | 46.8 | Trading Economics | — | — | **secondary only** |
| pmi | 2026-06-01 | 46.0 | Trading Economics | — | — | **secondary only** |
| gdp_growth_fy | 2025-07-01 | 5.1 | Al Arabiya | 5.1 | Central Bank of Egypt — MPC press release | **confirmed** |
| lng_imports | 2026-01-01 | 8.8 | MENA Market Lab (Smartkarma) | — | — | **secondary only** |
| gas_import_budget | 2026-07-01 | 10.7 | SEE News | — | — | **secondary only** |
| brent_fut | 2026-10-16 | 109.86 | Trading Economics | 109.86000061035156 | Yahoo Finance BZ=F (unofficial) | **confirmed** |
| fuel_95 | 2026-10-15 | 24.0 | SEE News | — | — | **secondary only** |
| fuel_92 | 2026-10-15 | 22.25 | SEE News | — | — | **secondary only** |
| fuel_80 | 2026-10-15 | 20.75 | SEE News | — | — | **secondary only** |
| fuel_diesel | 2026-10-15 | 20.5 | SEE News | — | — | **secondary only** |
| fuel_cng | 2026-10-15 | 13.0 | SEE News | — | — | **secondary only** |
| gold_eg_21k | 2026-10-16 | 6245 | Daily News Egypt | — | — | **secondary only** |
| xauusd_spot | 2026-10-16 | 4157.85 | Daily News Egypt | — | — | **secondary only** |
