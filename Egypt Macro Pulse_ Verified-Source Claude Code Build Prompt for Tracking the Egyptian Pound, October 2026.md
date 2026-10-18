# Egypt Macro Pulse: Final Claude Code Build Prompt (verified sources, October 2026)

Your existing draft is a strong core, but it was missing about half of what actually moves the pound: the external-sector flows (remittances, tourism, Suez, balance of payments, debt-service schedule), the energy import chain (LNG cargoes, fuel-pricing committee), structured geopolitical data, and a sector module for drug pricing — and one input in your concept list is already out of date: Moody's upgraded Egypt to B3 (positive) from Caa1 on 16 October 2026.\[1\] The prompt below closes those gaps using free, programmatic sources wherever they exist, marks everything else MANUAL, and forces Claude Code to verify every endpoint in Phase 0 before writing a single collector.

## TL;DR
- **Biggest additions:** IMF PortWatch daily chokepoint data (Suez, Bab el-Mandeb, Hormuz), the Caldara–Iacoviello GPR index (free, CC BY, monthly with country series plus a daily global series), the GDELT DOC 2.0 API (free, no key, rolling 3 months), CBE balance-of-payments/remittance/external-debt releases, the fuel-pricing committee and LNG trackers, and the new EDA drug-pricing Decision 480/2026 whose formula is 60% exchange rate, 30% urban inflation and 10% CBE deposit-rate change.
- **Not free or not programmatic:** ACLED API (Open tier for personal emails has no API; Research tier and above only), Egypt 5Y CDS and JPMorgan EMBI spreads (paid terminals), MSCI EM index levels, consensus forecasts (FocusEconomics/Reuters polls), Kpler tanker data, and full S&P Global PMI sub-indices — all are MANUAL or replaced with free proxies in the prompt.
- **Current state the tool must reproduce on day one (as of 18 Oct 2026):** CBE overnight deposit 19.00% (held five meetings in a row, next MPC 29 Oct), urban CPI 13.9% and core 14.1% in September, NIR a record $57.35bn, Brent near $110 vs a $75 budget assumption, fuel prices frozen through December 2026, USD/EGP around 53.45, and the IMF EFF ending 15 December 2026.

## Key Findings

| Area | What was added vs your draft | Verified source / access | Status |
|---|---|---|---|
| Shipping & chokepoints | Daily Suez Canal (chokepoint1), Bab el-Mandeb and Hormuz transits and tonnage | IMF PortWatch "Daily Chokepoints Data" on ArcGIS (CSV/GeoServices API, no key)\[2\] | Free, programmatic |
| Suez revenue | FY revenue, monthly SCA statements | Suez Canal Authority statements via press (FY2025/26 = $4.67bn, +23%)\[3\] | MANUAL |
| Remittances, BoP, current account | Monthly remittances, quarterly BoP | CBE press releases (FY2025/26 remittances $47.3bn; current-account deficit $22.5bn)\[4\]\[5\] | MANUAL/scrape (PDF) |
| External debt & service | Stock, short-term debt, projected service schedule | CBE external-debt releases; World Bank/IMF tables | MANUAL/scrape |
| Tourism | Arrivals and receipts | CBE BoP (receipts), IDSC/Ministry statements (arrivals) | MANUAL |
| Energy chain | LNG cargoes, gas import bill, load-shedding flag, fuel committee decisions | Ministry of Petroleum statements, EnterpriseAM/S&P Global reporting | MANUAL (events) |
| Geopolitical risk | Global GPR (daily + monthly), threats/acts sub-indices, country GPR | matteoiacoviello.com/gpr.htm (CC BY)\[6\] | Free, file download |
| News tone/volume | Egypt and region tone/volume timelines | GDELT DOC 2.0 API (no key, 250 records max, 3-month window)\[7\] | Free, programmatic |
| Conflict events | Event counts for Egypt/Red Sea/Gulf | ACLED | API **not** available on Open tier → MANUAL aggregated only\[8\] |
| Ratings | Full current state + upgrade logic | Fitch B stable (8 Oct), S&P B/B stable (Oct), Moody's B3 positive (16 Oct, upgraded from Caa1)\[9\]\[10\] | MANUAL (events) |
| IMF | Review calendar, disbursements, program end | IMF press releases (EFF extended to 15 Dec 2026; IMF Press Release No. 26/271 of 30 Jul 2026: 7th review lets Egypt draw about $1.5bn EFF + $272mn RSF) | MANUAL (events) |
| Healthcare module | EDA Decision 480/2026 repricing formula, CPI health sub-index | EDA decision as reported by Zawia3/EnterpriseAM; CAPMAS CPI\[11\]\[12\] | MANUAL + derived |
| Calendars | MPC, FOMC, CPI, PMI, NIR, GPR, PortWatch | CBE (8 meetings; remaining 29 Oct, 17 Dec); Fed (27–28 Oct, 8–9 Dec)\[13\]\[14\] | Seeded + verified |
| Paid / unavailable | CDS, EMBI, MSCI EM levels, consensus, Kpler, full PMI | Bloomberg/Refinitiv/JPMorgan/MSCI/FocusEconomics/Kpler/S&P | "Ask before paid" |

Three findings change how the tool should reason:

1. **The external picture is "strong buffers, wider gap."** Remittances hit a record $47.3bn in FY2025/26 (+29.6%) and NIR reached a record $57.35bn at end-September 2026, yet the current-account deficit widened to $22.5bn from $15.4bn as imports topped $108bn (petroleum imports ~$24.9bn).\[4\]\[5\]\[15\] The rule engine must therefore weigh flows (remittances, tourism, Suez, portfolio) against the import bill, not read record reserves as "no pressure."
2. **Oil is the dominant live shock.** Brent closed at $109.86 on 16 October 2026 against a $75 budget assumption; the IMF, as reported by The Middle East Observer (8 Oct 2026), estimates that "every $10-a-barrel increase in international oil prices would widen Egypt's current-account deficit by about 0.3% of GDP on an annual basis" (and that the energy import bill rose about $3.5bn between March and June 2026), which implies roughly 1% of GDP of annualized pressure at today's gap — treat this as secondary until checked against the IMF staff report. The fuel committee chose on 15 October to freeze prices through December, so the inflation pass-through is deferred, not cancelled — a classic lagged second-round risk for Q1 2027.\[16\]
3. **Gold currently signals no hidden devaluation.** On 16 October, 21K gold at EGP 6,245 and global gold at $4,157.85 imply a USD/EGP of about 53.4, essentially equal to the ~53.45 market rate;\[17\]\[18\] Marsad Al Dahab described local pricing swinging between a premium and a discount of about EGP 50/gram (≈0.8%), which is the normal noise band the tool should use before flagging anything.\[19\]

## The Prompt (copy everything inside the block into Claude Code)

````markdown
# BUILD: "Egypt Macro Pulse" — local Python tool for the Egyptian pound and economy

## 0. Context (read first)
I am Ehab: pricing & market research manager in healthcare (offshore from Egypt for a UAE hospital group), pharmacist by background, learning macroeconomics. I use VS Code + Claude Code and Power BI. This is a LEARNING tool, not financial advice. Timezone: Africa/Cairo. Today: 18 October 2026. Egyptian banks are closed Friday and Saturday; EGX trades Sunday–Thursday; global markets trade Monday–Friday.

Goal: collect, store, link (via cause-effect rules), and visualize EVERYTHING that drives USD/EGP and Egypt's economy — FX, monetary, inflation, external sector, fiscal/debt, real economy, energy, gold, global/US, political/geopolitical, and a healthcare-pricing module — so I get a complete picture with nothing missing.

Non-negotiable principles:
1. NEVER invent, interpolate, or "estimate" a data value. If a value is missing, store NULL with a reason and show "no data" in outputs.
2. Every number shown anywhere must carry: source name, source URL, observation date, release date, retrieved_at timestamp.
3. Ask me before creating any account, using any API key, or touching any paid source. Free, keyless sources first.
4. Prefer official primary sources (CBE, CAPMAS, MoF, IMF, Fed, FRED, EIA, ECB, Eurostat, World Bank). Use press/aggregators only as fallback and flag them with quality_flag = "secondary".
5. Explain every signal in plain cause→effect language (the rules below), so I learn from the output.

## 1. Tech stack
- Python 3.11+, uv or venv; packages: requests, httpx, pandas, pyarrow, pydantic, PyYAML, sqlite3/SQLAlchemy, feedparser, beautifulsoup4, pdfplumber (CBE PDFs), openpyxl/xlrd (GPR Excel), yfinance (market proxies, flagged "unofficial"), fredapi OR plain FRED REST (key needed — ASK ME), gdeltdoc (GDELT DOC 2.0), plotly, jinja2, pytest, python-dateutil, zoneinfo.
- Storage: SQLite (`data/pulse.db`) + Parquet exports.
- Outputs: static mobile-first HTML dashboard (Plotly + Jinja), Markdown/HTML daily brief, weekly deep-dive, Power BI exports (CSV + Parquet, star schema).
- Config: `config/sources.yaml`, `config/series.yaml`, `config/rules.yaml`, `config/indices.yaml`, `config/events_taxonomy.yaml`, `config/calendar_2026.yaml`.
- Secrets: `.env` (never committed). `.gitignore` must include `.env`, `data/`, `exports/`.

## 2. Phase 0 — Source verification (MUST run before any collector code)
Create `scripts/verify_sources.py` that, for every entry in `config/sources.yaml`:
- requests the URL/endpoint, records HTTP status, content type, last-modified, a 200-character sample, and whether login/API key is required;
- confirms the exact series ID / column name exists (e.g., FRED series metadata, GPR Excel column for Egypt, PortWatch `portid` = chokepoint1 for Suez Canal);
- writes `reports/phase0_source_audit.md` with a table: source | status (OK / BLOCKED / PAID / LOGIN / MOVED / MANUAL) | frequency observed | latest observation date | notes.
STOP after Phase 0 and show me the audit. Do not build collectors for anything not marked OK; mark them MANUAL.

Known facts to verify (from my research, Oct 2026):
- IMF PortWatch publishes "Daily Chokepoints Data" (daily transit calls and estimated trade volume in metric tons for 28 chokepoints) on ArcGIS Online with CSV download and GeoServices API links; Suez Canal = `chokepoint1`. The PortWatch Data & Methodology page states "Daily Chokepoint Transit Calls and Trade Volume Estimates — Updated Weekly, Tuesdays 9 AM ET"; verify Bab el-Mandeb / Strait of Hormuz IDs.
- Caldara–Iacoviello GPR (https://www.matteoiacoviello.com/gpr.htm): monthly Excel updated at the beginning of each month (last update 1 Oct 2026) including country-specific indexes for 44 countries; daily Recent GPR Excel updated every Monday (last 13 Oct 2026); sub-indices GPRT (threats) and GPRA (acts); license Creative Commons BY (credit authors).\[6\] Verify the Egypt column (expected mnemonic like `GPRC_EGY`) exists; if not, mark MANUAL and use global GPR + GDELT Egypt tone.
- GDELT DOC 2.0 API: `https://api.gdeltproject.org/api/v2/doc/doc` with `mode=timelinetone|timelinevol|timelinevolraw|artlist`, no key, rolling ~3-month window, max 250 records per artlist call. Respect rate limits (sleep ≥6s between calls).\[7\]\[20\]
- ACLED: API requires a myACLED account; the Open tier (assigned to personal/generic emails) has NO API access; API starts at Research tier (event data lagged 12 months).\[8\]\[21\]\[22\] Default = MANUAL (aggregated weekly downloads only). ASK ME before registering.
- S&P Global Egypt PMI: headline free in press release at pmi.spglobal.com (embargo 07:15 Cairo time, ~3rd business day of month);\[23\] sub-indices are paid → headline only.
- CBE (cbe.org.eg): MPC press releases, NIR monthly release (~7th of month), inflation note (core CPI), BoP press-release PDFs, external debt, monetary statistics (M2, private credit, NFA), T-bill/T-bond auction results. Many pages are HTML/PDF — scrape politely, cache raw files under `data/raw/`.
- CAPMAS (capmas.gov.eg): CPI release (~10th of month; September 2026 released Saturday 10 Oct).\[24\]\[25\]\[26\] PDFs/Arabic pages — scrape or MANUAL.
- FRED (needs free API key — ASK ME): verify these IDs exist and are current: DFF, FEDFUNDS, DGS10, DGS2, T10YIE, CPIAUCSL, CPILFESL, PAYEMS, UNRATE, VIXCLS, DTWEXBGS, DEXUSEU, DCOILBRENTEU, DCOILWTICO, DHHNGSP, PNGASEUUSDM, PWHEAMTUSDM, BAMLEMCBPIOAS (EM corporate OAS as EMBI proxy). Do NOT use the discontinued LBMA gold series; use another gold source (below).
- EIA Open Data API v2 (free key — ASK ME) for Brent/WTI spot and STEO forecasts.
- IMF data (SDMX/JSON API at data.imf.org), World Bank API (api.worldbank.org/v2), ECB Data Portal API, Eurostat API — verify endpoints and Egypt/euro-area series codes.
- Fed FOMC calendar: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm. \[13\]

## 3. Indicator catalog (series.yaml)
For each series store: id, name_en, name_ar, domain, frequency, unit, primary_source, endpoint/series_id, fallback, access (FREE_API / FREE_FILE / SCRAPE / MANUAL / PAID), definition_note, release_lag_days, stale_after_days.

### 3.1 Egypt FX & markets
| id | indicator | freq | primary | fallback | access |
|---|---|---|---|---|---|
| fx_cbe_official | USD/EGP CBE official (buy/sell) | daily (Sun–Thu) | CBE exchange-rates page | NBE, Banque Misr pages | SCRAPE |
| fx_market | USD/EGP market close | daily | yfinance `EGP=X` (unofficial) | Investing/XE (scrape, ToS check) | FREE_API (flag unofficial) |
| fx_parallel | Parallel-market rate | ad hoc | MANUAL entry with source URL | — | MANUAL |
| fx_gold_implied | Gold-implied USD/EGP | daily | DERIVED (see §5) | — | DERIVED |
| egx_foreign_net | EGX foreigners' net buy/sell (equities) | daily | EGX daily bulletin | press | SCRAPE/MANUAL |
| foreign_tbills_holdings | Non-resident holdings of T-bills | monthly | CBE monetary statistics | press | SCRAPE/MANUAL |
| tbill_auctions | T-bill yields (91/182/273/364d), bid-to-cover, accepted vs offered | per auction | CBE auction results | MoF, press | SCRAPE |
| eurobond_yields | Egypt USD Eurobond yields (key maturities) | daily | MANUAL / worldgovernmentbonds (ToS check) | — | MANUAL/PAID |
| cds_5y | Egypt 5Y CDS (bps) | daily | PAID (Bloomberg/Refinitiv) | MANUAL weekly from press | MANUAL |

### 3.2 Monetary
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| cbe_odr / cbe_olr / cbe_mainop / cbe_discount | CBE corridor (deposit, lending, main operation, discount) | per MPC | CBE MPC press releases | SCRAPE |
| cbe_mpc_statement | MPC statement text + tone tags (hawkish/dovish words) | per MPC | CBE | SCRAPE |
| interbank_overnight | Overnight interbank rate | daily | CBE | SCRAPE |
| m2 | Broad money M2 (y/y) | monthly | CBE monthly statistical bulletin | SCRAPE/MANUAL |
| credit_private | Bank credit to private sector vs to government (y/y and share) | monthly | CBE | SCRAPE/MANUAL |
| nfa_banks / nfa_cbe | Net foreign assets: banking system, CBE, commercial banks | monthly | CBE | SCRAPE/MANUAL |
| nir | Net international reserves (total, gold, FX, SDR) | monthly (~7th) | CBE NIR release | SCRAPE |
Seed values: corridor 19.00 / 20.00 / 19.50, discount 19.50 (unchanged since 12 Feb 2026 cut).\[14\]\[27\]\[28\]\[29\] NIR end-Sep 2026 = $57,348.2mn (gold $17.456bn, FX $39.292bn, SDR $0.602bn).\[30\]\[31\]

### 3.3 Inflation
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| cpi_urban_yoy / mom | Urban headline CPI | monthly (~10th) | CAPMAS | SCRAPE/MANUAL |
| cpi_national_yoy | Nationwide CPI | monthly | CAPMAS | SCRAPE/MANUAL |
| cpi_core_yoy / mom | Core CPI | monthly | CBE inflation note | SCRAPE |
| cpi_food_yoy / mom | Food & non-alcoholic beverages | monthly | CAPMAS | SCRAPE/MANUAL |
| cpi_health_yoy | Health sub-index (incl. medical products) | monthly | CAPMAS | MANUAL |
| infl_expectations | CBE projected inflation path / survey | per MPR | CBE Monetary Policy Report | MANUAL |
| infl_target | CBE target (7% ±2 by H2 2027)\[26\] | static | CBE | MANUAL |
Seed: Sep 2026 urban 13.9% y/y (1.3% m/m), core 14.1%, nationwide 12.8%; CBE projects FY2026/27 average 16.6%.\[26\]\[28\]\[32\]

### 3.4 External sector
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| remittances | Remittances of Egyptians abroad | monthly | CBE press release | SCRAPE/MANUAL |
| bop_ca | Current account balance | quarterly | CBE BoP press-release PDF | SCRAPE (pdfplumber) |
| bop_overall | Overall BoP | quarterly | CBE | SCRAPE |
| trade_oil / trade_nonoil | Oil and non-oil trade balance, exports, imports | quarterly (CBE), monthly (CAPMAS) | CBE / CAPMAS | SCRAPE/MANUAL |
| tourism_receipts | Tourism revenues | quarterly | CBE BoP | SCRAPE |
| tourism_arrivals | Tourist arrivals | monthly/periodic | IDSC/Ministry of Tourism/CAPMAS | MANUAL |
| suez_revenue | Suez Canal revenue | monthly/annual | SCA statements | MANUAL |
| suez_transits | Suez daily transits + capacity | daily (weekly update) | IMF PortWatch chokepoint1 | FREE_API |
| babelmandeb_transits / hormuz_transits | Chokepoint transits | daily | IMF PortWatch | FREE_API |
| fdi_net | Net FDI inflows | quarterly | CBE BoP | SCRAPE |
| portfolio_net | Portfolio investment net | quarterly | CBE BoP | SCRAPE |
| gulf_deals | Gulf deposits / mega-deals (Ras El Hekma type), privatization/IPO proceeds | event | MANUAL events table | MANUAL |
Seed (FY2025/26, CBE release 12 Oct 2026): remittances $47.3bn (+29.6%); current-account deficit $22.5bn (vs $15.4bn); imports >$108bn (non-petroleum $83.9bn, petroleum ~$24.9bn); Jan–Aug 2026 remittances $33.9bn.\[4\]\[33\] Suez FY2025/26 revenue $4.67bn (+23%; record was $9.4bn in FY2022/23). Tourism Jan–Aug 2026: 12.7m arrivals, $12bn (IDSC).\[3\]\[5\]\[34\]\[35\]

### 3.5 Fiscal & debt
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| ext_debt_stock | External debt (total, by borrower, short-term) | quarterly | CBE external debt bulletin | SCRAPE/MANUAL |
| ext_debt_service_actual | Actual external debt service (principal + interest) | quarterly | CBE | MANUAL |
| ext_debt_service_sched | Projected MLT public & publicly guaranteed service by year | annual/semiannual | CBE projected debt-service tables; World Bank IDS | MANUAL |
| eurobond_maturities | Eurobond/sukuk maturity ladder (date, amount, coupon) | static + events | MoF investor relations / prospectuses | MANUAL |
| budget_balance / primary_balance | Overall and primary balance (% GDP) | monthly/annual | MoF financial monthly | SCRAPE/MANUAL |
| gov_debt_gdp | General government debt % GDP | annual | MoF / IMF | MANUAL |
| interest_to_revenue | Interest payments / revenue | annual | MoF / rating reports | MANUAL |
| budget_oil_assumption | Budget oil price assumption | per budget | MoF (FY2026/27 = $75/bbl)\[36\] | MANUAL |
| dom_debt_maturities | T-bill maturity wall (EGP) | monthly | CBE/MoF | MANUAL |
| imf_program | Reviews, disbursements, program end | event | IMF press releases | MANUAL (events) |
| ratings | Fitch/S&P/Moody's rating + outlook | event | agency press releases | MANUAL (events) |
| forecasts | IMF WEO/Article IV, World Bank MPO, agency forecasts (GDP, CPI, CA, debt) | per publication | IMF/WB/agencies | MANUAL |
| consensus | Consensus (Reuters poll, FocusEconomics) | per poll | PAID/press | MANUAL |
IMPORTANT: debt-service numbers differ by definition (calendar vs fiscal year, PPG vs total, with/without short-term rollover and CBE deposits). Always store `definition_note`. Seed: external debt $164.8bn end-Mar 2026 (38.9% of GDP); actual debt service $28.3bn in first 9 months of FY2025/26; CBE-projected MLT PPG service $34.6bn (2026), $19.6bn (2027), ~$14.6bn (2028) as reported by The Edge citing CBE; ADCB estimated FY2025/26 repayments at $28.2bn.\[37\]\[38\]\[39\] Ratings: Fitch B/Stable (affirmed 8 Oct 2026), S&P B/B/Stable (affirmed Oct 2026), Moody's B3/Positive (upgraded from Caa1 on 16 Oct 2026).\[1\]\[10\]\[40\] IMF: 5th+6th EFF reviews completed 25 Feb 2026 (~$2.3bn); EFF extended through 15 Dec 2026; 7th review completed per IMF Press Release No. 26/271 (30 Jul 2026), allowing Egypt to draw SDR 1.11bn (about $1.5bn) under the EFF and SDR 200mn (about $272mn) under the RSF, bringing total drawings under both arrangements to SDR 5.4bn (about $7.3bn).

### 3.6 Real economy
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| pmi | S&P Global Egypt PMI (headline) | monthly | pmi.spglobal.com press release | SCRAPE |
| pmi_implied_gdp | PMI-implied GDP growth = PMI × 0.269 − 8.62 (S&P Global formula)\[23\] | monthly | DERIVED | DERIVED |
| gdp_growth | Real GDP growth (quarterly/FY) | quarterly | Ministry of Planning / CAPMAS | MANUAL |
| unemployment | Unemployment rate | quarterly | CAPMAS LFS | MANUAL |
| gas_production / gas_imports | Domestic gas output, pipeline + LNG imports | monthly/periodic | Ministry of Petroleum, JODI Gas | MANUAL / FREE_FILE |
| lng_cargoes | LNG cargoes per month | monthly | ministry statements / press (Kpler is PAID) | MANUAL |
| load_shedding | Load-shedding active (0/1) + hours | event | EEHC / Ministry of Electricity | MANUAL (events) |
| wheat_imports | Wheat purchases/tenders, strategic reserve months | event/monthly | Ministry of Supply statements | MANUAL |
Seed: PMI Sep 2026 47.2 (Aug 49.6, Jul 46.8, Jun 46.0). GDP FY2025/26 5.1%.\[41\] LNG imports 1H 2026 = 8.8 bcm (more than doubled y/y); FY2026/27 gas import budget $10.7bn; summers 2025 and 2026 passed without load-shedding.\[42\]\[43\]\[44\]\[45\]

### 3.7 Energy & commodities
| id | indicator | freq | primary | fallback | access |
|---|---|---|---|---|---|
| brent | Brent spot | daily | FRED DCOILBRENTEU / EIA API | yfinance BZ=F | FREE_API |
| wti | WTI | daily | FRED DCOILWTICO / EIA | yfinance CL=F | FREE_API |
| henry_hub | Henry Hub gas | daily | FRED DHHNGSP | — | FREE_API |
| ttf | European gas (TTF) | monthly/daily | FRED PNGASEUUSDM (monthly) | yfinance TTF=F (unofficial) | FREE_API |
| wheat | Wheat (CBOT) | daily/monthly | yfinance ZW=F; FRED PWHEAMTUSDM (monthly) | World Bank Pink Sheet | FREE_API |
| eia_steo_brent | EIA STEO Brent forecast | monthly | EIA STEO | — | FREE_API |
| opec_decisions | OPEC+ decisions | event | OPEC press releases | — | MANUAL (events) |
| freight | Container/tanker freight (e.g., Drewry WCI headline) | weekly | press headline | — | MANUAL |
| fuel_prices_egypt | Egypt pump prices (92/95/80 octane, diesel, CNG, LPG cylinder) | per committee decision | Ministry of Petroleum | — | MANUAL (events) |
Seed: Brent $109.86 on 16 Oct 2026. Fuel committee 15 Oct 2026: prices unchanged through end-December 2026 — 95 octane EGP 24.00, 92 octane EGP 22.25, 80 octane EGP 20.75, diesel EGP 20.50, CNG EGP 13/m³; last hike March 2026;\[46\]\[47\] quarterly mechanism resumed July 2026.\[16\]\[48\]\[49\]\[50\]\[51\]

### 3.8 Gold
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| xauusd | Global gold spot (USD/oz) | daily | yfinance GC=F (unofficial) / metals API (ASK ME) | FREE_API |
| xagusd | Silver (optional) | daily | yfinance SI=F | FREE_API |
| gold_eg_21k / 24k / pound | Egypt 21K/24K per gram, gold pound (8g 21K) | daily | iSagha / goldpricez / banklive (scrape, ToS check) | SCRAPE |
| cb_gold_buying | Central-bank gold purchases | monthly/quarterly | World Gold Council (free registration may be required — ASK ME) | MANUAL |
| cbe_gold_reserves | CBE gold holdings ($) | monthly | CBE NIR release | SCRAPE |

### 3.9 Global / US
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| fed_funds | Effective fed funds | daily | FRED DFF | FREE_API |
| fomc | FOMC decisions + statement surprise vs expectations | per meeting | federalreserve.gov | SCRAPE |
| us_cpi / us_core_cpi | CPI, core CPI | monthly | FRED CPIAUCSL / CPILFESL (or BLS API) | FREE_API |
| us_nfp / us_unemp | Payrolls, unemployment | monthly | FRED PAYEMS / UNRATE | FREE_API |
| us10y / us2y / breakeven | Treasury yields, 10Y breakeven | daily | FRED DGS10 / DGS2 / T10YIE | FREE_API |
| usd_broad | Broad dollar index | daily | FRED DTWEXBGS | FREE_API |
| dxy | ICE DXY | daily | yfinance DX-Y.NYB (unofficial) | FREE_API |
| vix | VIX | daily | FRED VIXCLS | FREE_API |
| em_spread_proxy | EM credit spread proxy | daily | FRED BAMLEMCBPIOAS (verify) | FREE_API |
| msci_em_proxy | EM equities proxy | daily | yfinance EEM (ETF, not the index) | FREE_API |
| eurusd | EUR/USD | daily | FRED DEXUSEU | FREE_API |
| euro_area | Euro-area GDP, HICP, PMI headline | monthly/quarterly | Eurostat / ECB Data Portal APIs | FREE_API |
| gulf_health | Saudi/UAE PMI headline, oil output, GCC fiscal breakevens | monthly | S&P PMI press; OPEC MOMR; IMF REO | MANUAL |

### 3.10 Political & geopolitical
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| gpr_global | GPR global (monthly + daily), GPRT, GPRA | monthly / daily (Mon) | matteoiacoviello.com/gpr.htm Excel | FREE_FILE |
| gpr_egypt | Country GPR Egypt (+ Israel, Iran, Saudi Arabia if available) | monthly | same Excel (verify column) | FREE_FILE |
| gdelt_egypt_tone / vol | Tone and volume for queries: Egypt economy, Egyptian pound, Suez Canal, Red Sea shipping, Strait of Hormuz, Iran war, Gaza | daily | GDELT DOC 2.0 timelinetone/timelinevol | FREE_API |
| acled_counts | Conflict events (Egypt, Yemen/Red Sea, Iran, Israel/Gaza) | weekly | ACLED aggregated (Open tier) | MANUAL |
| news_rss | Headlines: Ahram Online, Daily News Egypt, EnterpriseAM, Arab Finance, Mada Masr, Egypt Independent, IMF press, CBE news, Reuters (if RSS available) | hourly | RSS (verify each feed) | FREE (RSS) |
| political_calendar | Elections, cabinet changes, budget submission, IMF missions, EU macro-financial assistance tranches, Gulf summits | event | MANUAL | MANUAL |
| sanctions | Sanctions events affecting Egypt's partners / shipping | event | OFAC/EU press | MANUAL |

### 3.11 Healthcare-sector module (optional, Phase 7)
| id | indicator | freq | primary | access |
|---|---|---|---|---|
| eda_decisions | EDA pricing decisions (Decision 480/2026 and successors), repricing approvals/denials | event | EDA site / Official Gazette / press | MANUAL (events) |
| eda_repricing_index | DERIVED EDA formula tracker (see §5) | monthly | DERIVED | DERIVED |
| cpi_health / cpi_med_products | CAPMAS health & medical products sub-indices | monthly | CAPMAS | MANUAL |
| drug_shortages | Official shortage statements (% of market), NGO reports | event | EDA/Ministry of Health/press | MANUAL |
| pharma_market | Market size / sales growth (IQVIA via press) | quarterly | press | MANUAL |
Seed: Decision 480/2026 (published in the Official Gazette, issue 210 bis (H), on 23 Sep 2026 per Zawia3; effective ~24 Sep) replaced Decree 499/2012; repricing formula weights, confirmed by law firm ADSERO (24 Sep 2026): exchange rate 60%, urban inflation 30%, change in CBE overnight deposit rate 10%; computed every 6 months (or earlier in exceptional conditions); a price move requires the computed change ≥10% sustained ≥45 days; increases only on the license holder's request; reference basket cut to 15 countries. Last general drug repricing was October 2024 (priced at EGP 50/USD); on 15 Oct 2026 Pharma Division head Ali Ouf said there is "no intention to raise any drug prices under the current circumstances," separately told Masrawy (per Zawia3) that increases would not happen unless the pound weakens past EGP 55/USD for 45 days, and Egypt Independent/Al-Masry Al-Youm (15 Oct) reported the EDA "rejected approximately 90 percent of the price adjustment requests." CAPMAS Sep 2026: health +5.2% y/y nationwide; medical products/appliances −1.3% y/y (secondary sources).\[52\]

## 4. Data model (SQLite)
- `series_catalog(series_id PK, name_en, name_ar, domain, frequency, unit, source, endpoint, access, definition_note, stale_after_days)`
- `observations(series_id, obs_date, value REAL NULL, unit, release_date, retrieved_at, source_url, vintage, quality_flag CHECK IN ('official','secondary','unofficial','manual','derived'), null_reason, PRIMARY KEY(series_id, obs_date, vintage))`
- `raw_files(file_id, source, url, sha256, retrieved_at, path)` — keep raw PDFs/Excel for audit.
- `fetch_log(run_id, source, started_at, status, rows_added, error)`
- `calendar(event_date, event_time_cairo, kind, series_id, description, status CHECK IN ('scheduled','confirmed','done','moved'), source_url)`
- `events(event_id PK, event_date, event_type, domain, title_en, title_ar, severity INT 1..5, direction INT -1/0/+1 (+1 = more pressure on EGP to weaken), half_life_days, expires_at, confidence CHECK IN ('confirmed','reported','candidate'), source_name, source_url, entered_by CHECK IN ('manual','auto_candidate'), notes)`
- `event_types(event_type PK, default_severity, default_direction, default_half_life_days, affects_subindex, description)`
- `rule_hits(run_date, rule_id, fired BOOL, strength REAL, inputs_json, explanation_en, explanation_ar)`
- `index_values(run_date, index_id, value REAL, components_json, coverage_pct)`
- `manual_inputs` sheet: `data/manual/manual_inputs.xlsx` (one tab per MANUAL series + events tab) imported with validation; every row needs source_url and date or it is rejected.

Event decay: `event_score(t) = severity × direction × 0.5^((t − event_date)/half_life_days)`; drop when < 0.1 or past `expires_at`. Only `confirmed` and `reported` events count; `candidate` events (auto-proposed from RSS/GDELT keyword rules) are shown in a review queue and NEVER enter indices until I confirm them.

events_taxonomy.yaml (defaults; I can edit):
| event_type | sev | dir | half-life (days) | sub-index |
|---|---|---|---|---|
| regional_war_escalation (Iran/Israel/Gulf) | 5 | +1 | 30 | Geopolitical |
| chokepoint_disruption (Hormuz/Bab el-Mandeb attacks) | 4 | +1 | 21 | Geopolitical/External |
| ceasefire_or_deescalation | 3 | −1 | 21 | Geopolitical |
| domestic_unrest | 3 | +1 | 14 | Geopolitical |
| cabinet_change / CBE governor change | 2 | 0 (tag) | 30 | Geopolitical |
| imf_staff_level_agreement | 3 | −1 | 45 | Fiscal |
| imf_board_approval_disbursement | 3 | −1 | 30 | Fiscal |
| imf_review_delay | 4 | +1 | 45 | Fiscal |
| rating_upgrade / outlook_positive | 3 | −1 | 60 | Fiscal |
| rating_downgrade / outlook_negative | 4 | +1 | 60 | Fiscal |
| gulf_deposit_or_megadeal | 4 | −1 | 60 | External |
| privatization_ipo_proceeds | 2 | −1 | 30 | External |
| eurobond_issuance_success | 2 | −1 | 30 | Fiscal |
| eurobond_maturity_due (within 30d) | 2 | +1 | 7 | Fiscal |
| fuel_price_hike | 3 | +1 (inflation) | 90 | Commodities/Inflation |
| fuel_price_freeze | 1 | 0 (tag deferred pass-through) | 90 | Commodities |
| load_shedding_start | 3 | +1 | 30 | Commodities |
| lng_supply_disruption (e.g., Israeli gas cut) | 4 | +1 | 30 | Commodities |
| eu_mfa_tranche | 2 | −1 | 30 | External |
| sanctions_on_partner_or_shipping | 3 | +1 | 45 | Geopolitical |
| eda_repricing_decision | 2 | 0 (healthcare tag) | 180 | Healthcare |

## 5. Derived metrics (all formulas in `pulse/derive.py`, unit-tested)
- Real policy rates: `real_headline = cbe_odr − cpi_urban_yoy`; `real_core = cbe_odr − cpi_core_yoy`; `real_expected = cbe_odr − infl_expectations` (also vs corridor ceiling cbe_olr). Example check (Sep 2026): 19.0 − 13.9 = +5.1 pp; 19.0 − 14.1 = +4.9 pp; 19.0 − 16.6 = +2.4 pp; corridor top 20.0 − 13.9 ≈ +6.1 pp.\[28\]
- Carry: `carry_usd_ret_ex_ante = tbill_12m_yield − expected_depreciation` (expected_depreciation from `fx_gold_implied` gap or MANUAL forward/NDF if available); `carry_ex_post_3m = tbill_3m_yield/4 − %Δ USD/EGP over the 3 months`. Never fabricate a forward rate.
- Gold-implied FX: `fx_gold_implied = gold_eg_21k / (xauusd / 31.1035 × 0.875)` (24K uses 0.999). `gold_gap_pct = fx_gold_implied / fx_cbe_official − 1`. Local premium in EGP/gram = local 21K − (xauusd/31.1035 × 0.875 × fx_cbe_official). Timestamp-align (use same Cairo hour; flag if > 6h mismatch). Sanity check: 16 Oct 2026, 21K EGP 6,245 and XAU $4,157.85 → implied ≈ 53.4 vs market ≈ 53.45 → gap ≈ 0%.\[17\]\[18\]
- FX momentum & volatility: 1d/5d/20d % change, 20d realized vol; "flat official rate" flag = 20d abs change < 0.3%.
- Hidden-peg detector inputs: NIR 3-month change, FX 20d change, gold_gap_pct, fx_parallel gap, NFA trend.
- Real exchange rate: `rer_index = nominal USD/EGP × (US CPI / Egypt CPI)` rebased (choose base period in config, default Mar 2024 float); over/undervaluation = deviation from 5-year average (label as rough heuristic).
- Oil: `brent_gap = brent − budget_oil_assumption`; `ca_pressure_pct_gdp ≈ 0.03 × brent_gap/1` (IMF rule of thumb: +$10/bbl ≈ +0.3% of GDP on the current-account deficit)\[53\] — label "IMF rule-of-thumb"; `brent_egp = brent × USD/EGP`; quarter-average Brent and USD/EGP vs previous quarter (mirrors the fuel committee's inputs).
- External coverage: `nir_months_imports = nir / (annual imports/12)`; `nir_to_st_debt`; `debt_service_next12m / nir`; `remittances_12m_sum`, y/y; `suez_transits_7dma` vs pre-crisis baseline (2023 average, computed from PortWatch history — do not hardcode).
- Fiscal: `interest_to_revenue`, primary balance vs IMF target.
- PMI: 3-month average, distance from 50, PMI-implied GDP.
- Surprise vs consensus: `surprise = actual − consensus` for CPI, MPC, FOMC, PMI when consensus is entered (MANUAL); MPC tone: hold/cut/hike vs consensus → hawkish/dovish surprise.
- EDA tracker (healthcare): `eda_signal = 0.6 × %Δ USD/EGP + 0.3 × Δ urban CPI index % + 0.1 × Δ cbe_odr %` over the 6-month window; flag when ≥10% and sustained ≥45 days. Label clearly "my reconstruction of Decision 480 as reported in press; verify against Gazette text."

## 6. Rule engine (rules.yaml)
Each rule: `id, domain, condition (pandas-evaluable on latest values), strength (0..1 formula), direction (+1 pressure on EGP / −1 relief), affects (subindex list), lag_note, explanation_en, explanation_ar, concept_tag` (links to the concept I learned). Thresholds are DEFAULTS in config, not facts — label them "tool default" in outputs.

Required rules (implement all; add more if useful):
FX & markets
- FX01 hidden_peg: NIR falling 3 months AND official FX flat 20d AND (gold_gap_pct > 5% OR parallel gap > 5%) → +1, strong. Concept: hidden peg.
- FX02 parallel_gap: parallel or gold-implied gap > 3% watch, > 5% alert, > 10% severe → +1. Noise band ±0.8% (≈ EGP 50/gram on 21K) = ignore.
- FX03 foreign_outflow: EGX foreign net selling 5 sessions in a row OR T-bill non-resident holdings fall > 5% m/m → +1. Concept: hot money.
- FX04 auction_stress: bid-to-cover < 1.2 or accepted < 70% of offered, or yields up > 100 bp in 4 weeks → +1. Concept: crowding out / financing stress.
- FX05 sharp_move: USD/EGP 5d change > 2% → alert (devaluation/float adjustment).
Monetary & inflation
- MO01 real_rate_cushion: real_headline < +2 pp → +1 (carry less attractive); > +5 pp → −1.
- MO02 real_rate_core_vs_expected divergence > 3 pp → flag "expectations risk".
- MO03 mpc_surprise: decision differs from consensus → hawkish (−1) / dovish (+1). Concept: market surprise.
- MO04 data_dependence: CPI m/m > 1.5% for 2 months → expect hawkish bias at next MPC (explain).
- MO05 passthrough: USD/EGP up > 5% in 3 months → expect core CPI acceleration in 1–6 months (lagged). Concept: pass-through.
- MO06 vicious_cycle: FX weakening AND CPI rising AND real rate falling → +1 strong. Concept: inflation vicious cycle.
- MO07 second_round: fuel/electricity hike event within 90 days AND core CPI m/m rising → flag second-round effects.
- MO08 crowding_out: credit to government growth > private-credit growth by 10 pp → growth-drag note (not FX).
External
- EX01 remittances_momentum: 3m y/y < 0 → +1; > 20% → −1.
- EX02 suez_weak: suez_transits_7dma < 60% of 2023 baseline → +1; recovery above 85% → −1.
- EX03 tourism_shock: regional_war_escalation active AND tourism data y/y falling → +1. Concept: triple hit.
- EX04 triple_hit: regional war event active AND Brent > budget+15 AND (portfolio outflow OR FX03 fired) → +1 strong. Concept: external shock triple hit.
- EX05 ca_gap: current-account deficit widening y/y > 30% → +1.
- EX06 reserves_cover: NIR < 5 months of imports → +1; record high NIR → −1 (but weigh against EX05).
- EX07 gulf_inflow: gulf_deposit_or_megadeal event active → −1.
Fiscal & debt
- FD01 debt_wall: external service due next 90 days / NIR > 10% → +1; Eurobond maturity within 30 days → watch.
- FD02 interest_burden: interest_to_revenue > 50% → structural +1 (slow-moving).
- FD03 imf_anchor: IMF program active and on track → −1; review delayed > 60 days vs schedule → +1; program end date within 60 days with no successor announced → watch (+0.5). Concept: IMF as guarantor.
- FD04 ratings: upgrade/positive outlook → −1; downgrade/negative → +1; note "ratings lag markets" — if CDS/Eurobond yields already moved > 100 bp in the same direction in prior 60 days, halve strength.
- FD05 eurobond_spread: Eurobond yield − US10Y > 700 bp → +1 (MANUAL input).
Real economy
- RE01 pmi_contraction: PMI < 50 for 3 months → growth-weak note; < 47 → stronger. Concept: trade-off inflation vs growth (raises cut-vs-hold dilemma).
- RE02 energy_stress: load_shedding event active OR LNG cargoes needed > budgeted → +1.
Energy & commodities
- EC01 oil_budget_gap: brent_gap > $10 → +1 (scale by gap; strong if > $25). Explain fiscal (subsidy/EGPC) + external (import bill) + inflation (fuel committee) channels.
- EC02 fuel_committee_lag: quarter-avg Brent in EGP up > 10% vs previous quarter AND fuel_price_freeze event → "deferred pass-through" warning for next quarter.
- EC03 gas_price: TTF or LNG proxy up > 30% in 1 month → +1 (Egypt LNG bill).
- EC04 wheat: wheat up > 20% in 3 months → +1 (import bill, bread subsidy).
- EC05 hormuz: chokepoint_disruption event or Hormuz transits < 50% baseline → +1, also feeds EC01.
Gold
- GO01 global_gold_up_usd_strong: gold up AND DXY up → risk-off/safe-haven note.
- GO02 local_gold_premium: local premium > 3% sustained 5 days → +1 (devaluation hedging); persistent discount → −1 (local dollar demand easing).
- GO03 gold_reserves_effect: CBE gold valuation ↑ explains part of NIR rise — decompose NIR change into FX vs gold (do not count gold revaluation as "new inflows").
Global
- GL01 fed_hawkish: FOMC surprise hawkish or US CPI above consensus → dollar ↑, EM outflow risk → +1.
- GL02 risk_off: VIX > 25 OR EM spread proxy +50 bp in 1 month → +1. Concept: safe havens.
- GL03 dxy_vs_egp: explain that DXY measures the dollar vs majors, while USD/EGP is driven by Egypt's own dollar supply/demand — fire when they diverge.
- GL04 euro_area_weak: euro-area PMI < 50 → tourism/exports headwind note.
- GL05 gulf_weak: GCC oil output cuts or Gulf PMI < 50 → remittances/investment risk.
Geopolitical
- GP01 gpr_spike: GPR daily 7d avg > 90th percentile of last 3 years → +1.
- GP02 gpr_egypt: Egypt country GPR > 2 std above 5-year mean → +1.
- GP03 gdelt_tone: Egypt-economy tone 7d avg drops > 2 std AND volume spike → +0.5 (weak; news-based).
- GP04 events: sum of active decayed event scores per sub-index (from events table) feeds the Geopolitical sub-index directly.
Healthcare (Phase 7)
- HC01 eda_trigger: eda_signal ≥ 10% sustained ≥ 45 days → "repricing requests likely eligible" note.
- HC02 fx_threshold: USD/EGP > 55 for 45 days (industry-cited trigger) → watch.
- HC03 import_cost: USD/EGP 3m change > 5% → imported medical supplies cost pressure note for UAE-vs-Egypt pricing.

Rule output style: each fired rule writes one sentence in English + one in Egyptian Arabic (no English words inside the Arabic sentence) + concept tag + the input values with dates.

## 7. Composite indices (indices.yaml)
- Pound Pressure Index (PPI), −100 (strong relief) .. +100 (strong pressure on EGP to weaken).
- Sub-indices, each −100..+100: External (25%), Monetary & Markets (20%), Fiscal & Debt (15%), Commodities/Energy (15%), Geopolitical (15%), Global/US (10%). Weights in config.
- Method: each input → z-score vs rolling 3-year window (min 24 obs; else use rule strengths only) → clip ±3 → map with `100 × tanh(z/2)` → sign so + = pressure → weighted mean of available inputs; events add decayed scores (scaled, capped at ±40 per sub-index).
- Store `coverage_pct` (share of weights with fresh data). If coverage < 60%, show the PPI greyed out with "insufficient data". Never fill gaps.
- Also publish an Inflation Pressure Index (pass-through, fuel lag, food, core momentum) and a Growth Index (PMI, credit, real rates) to show the trade-off.
- Backtest page: plot PPI vs USD/EGP 20d change for history where data exists (learning only; no predictive claims).

## 8. Outputs
1. Dashboard (`site/index.html`, mobile-first): header with PPI gauge + sub-index bars + coverage; tiles per domain (value, change, date, source link, stale badge); charts: USD/EGP official vs gold-implied, real rates, NIR decomposition (FX/gold/SDR), Brent vs $75 budget line, Suez 7dma vs baseline, remittances 12m sum, GPR daily, PMI with 50 line; "What fired today" rule list; events timeline with decay bars; review queue for candidate events; calendar of the next 14 days.
2. Daily brief (`briefs/YYYY-MM-DD.md` + HTML) in Egyptian Arabic: sections "الخلاصة"، "الجنيه النهارده"، "الفلوس الداخلة والخارجة"، "الفايدة والتضخم"، "البترول والدهب"، "السياسة والمنطقة"، "إيه اللي جاي في الأجندة". Arabic sentences must contain NO English words or Latin letters; numbers allowed. Every English term (e.g., carry trade, pass-through, CDS) goes ONLY in a separate glossary table at the end: | المصطلح بالعربي | English term | شرح بسيط |. Add a test that fails if Latin letters appear in brief body sentences.
3. Weekly deep-dive (Thursday evening, Cairo): English + Arabic summary, sub-index changes, top 5 rules by strength, chains explained step by step (e.g., war → Brent ↑ → import bill ↑ → CA deficit ↑ → FX pressure; and war → portfolio outflows → T-bill yields ↑), data-quality report (stale/missing).
4. Power BI export (`exports/`): `fact_observations`, `fact_index_values`, `fact_rule_hits`, `fact_events`, `dim_series`, `dim_date` (with Cairo business-day flag), `dim_source` — CSV + Parquet, ISO dates, UTF-8 BOM for Arabic.

## 9. Release calendar (calendar_2026.yaml — verify each in Phase 0, update monthly)
- CBE MPC 2026 (8 meetings): 12 Feb, 2 Apr, 21 May, 9 Jul, 20 Aug, 24 Sep, 29 Oct, 17 Dec.\[14\]
- FOMC: 27–28 Oct 2026, 8–9 Dec 2026 (SEP); 2027: 26–27 Jan, 16–17 Mar, 27–28 Apr, 8–9 Jun, 27–28 Jul, 14–15 Sep, 26–27 Oct, 7–8 Dec.\[13\]
- CAPMAS urban CPI: ~10th of each month (Oct CPI ≈ 10 Nov, after the 29 Oct MPC); CBE core CPI same/next day; CBE inflation analysis a few days later.
- S&P Global Egypt PMI: ~3rd business day, 07:15 Cairo.
- CBE NIR: ~5th–8th of each month.
- CBE BoP: quarterly (FY2025/26 full-year released 12 Oct 2026);\[54\] external debt: quarterly.
- GPR: monthly file ~1st of month; daily file every Monday.\[6\]
- IMF PortWatch: weekly, Tuesdays 9 AM ET (per the PortWatch Data & Methodology page).
- Fuel pricing committee: quarterly; current prices fixed through end-December 2026\[16\]\[49\] → next decision expected in or after January 2027 (status 'scheduled', unconfirmed).
- IMF: EFF arrangement ends 15 Dec 2026 (IMF press release);\[55\] record any final review/board date as events when announced.
- Ratings: EU-regulated agencies publish sovereign calendars — fetch Fitch/S&P/Moody's 2027 Egypt dates (MANUAL). Latest actions: Fitch 8 Oct, S&P Oct, Moody's 16 Oct 2026.
- T-bill/T-bond auctions: fetch CBE auction schedule (verify weekdays/tenors); EGX holidays: Egyptian public-holiday list.
- US CPI and payrolls: BLS schedule (fetch); Eurostat flash HICP (fetch).
- EDA: first six-month repricing calculation window ≈ mid-Feb 2027 (press estimate — tag 'unconfirmed').\[12\]

## 10. Scheduling
- `pulse run --job daily` at 09:30 and 18:30 Cairo (Sun–Thu); `--job global` at 23:30 Cairo Mon–Fri (after US close); `--job weekly` Thu 20:00; `--job gpr` Mon 12:00 and 2nd of month; `--job calendar` daily 07:00 (alerts for next-48h releases).
- Windows Task Scheduler XML templates (`ops/windows/*.xml`) and cron lines (`ops/cron.txt`); both use the venv Python with absolute paths; log to `logs/`.
- Retry with exponential backoff; per-source rate limits; polite User-Agent; cache raw responses.

## 11. Data integrity rules
- Never invent, carry forward silently, or interpolate. Weekend/holiday: show the last official value with its own date and a badge "سوق مقفول / market closed" — not a new observation.
- Stale flag: value older than `stale_after_days` (daily=3 business days, weekly=10, monthly=45, quarterly=120) → orange badge; older than 2× → red and excluded from indices.
- Vintages: keep revisions (CPI, BoP, GDP) as new vintages; indices use latest vintage; charts can show first release.
- Conflicts: if two sources disagree by > 0.5% for the same obs, store both, flag `conflict`, show primary.
- Unit tests for units (%, pp, bp, $bn vs $mn, EGP/gram), date alignment (Cairo vs UTC), and Fri/Sat handling.
- Every chart and table shows source + date in the caption.
- Secondary-source seeds in this prompt (marked "Seed") must be re-fetched from primary sources in Phase 1; if not confirmable, keep them with quality_flag='secondary'.

## 12. Testing
- pytest: formulas (real rates, gold-implied FX with the 16 Oct 2026 sanity case, PMI-implied GDP, decay), rule firing on synthetic fixtures, index bounds (−100..100), coverage logic, Arabic-no-Latin test, export schema test, calendar timezone test.
- `pulse doctor` command: checks DB integrity, stale series, failed sources, and missing manual inputs.

## 13. Phased build plan (stop at each checkpoint and show me results)
- Phase 0: source audit (§2). CHECKPOINT: I approve sources and any keys (FRED, EIA).
- Phase 1: core collectors — FX, CBE rates/NIR, CPI, PMI, Brent/WTI, gold global + Egypt, FRED US block. CHECKPOINT: dashboard v0 with 15 tiles.
- Phase 2: external & fiscal — PortWatch, BoP/remittances PDFs, external debt, auctions, manual_inputs.xlsx import. CHECKPOINT.
- Phase 3: global & commodities — DXY, VIX, EM proxies, gas, wheat, euro area, EIA STEO. CHECKPOINT.
- Phase 4: geopolitical — GPR files, GDELT timelines, RSS ingestion, events table + candidate review queue. CHECKPOINT.
- Phase 5: rule engine + indices + backtest page. CHECKPOINT: show which rules fire today and why.
- Phase 6: outputs — Arabic brief + glossary, weekly deep-dive, Power BI export. CHECKPOINT.
- Phase 7: healthcare module (EDA tracker, CPI health). CHECKPOINT.
- Phase 8: scheduling, tests, docs (`README.md` in English + `README_ar.md`).

## 14. Ask before
Creating any account (FRED, EIA, ACLED, World Gold Council), any paid data (CDS, EMBI, MSCI, Kpler, consensus, full PMI), scraping any site whose terms forbid it, or sending any data off my machine.
````

## Caveats
- **Your concept list needs one update:** Moody's is now B3 with a positive outlook (upgraded 16 October 2026), not Caa1.\[1\] The Fitch (8 October) and S&P (October) affirmations at B stable are confirmed.\[10\]\[56\]
- **The IMF end date conflicts between sources:** the IMF press release says the EFF runs through 15 December 2026,\[55\] while Fitch's commentary refers to the program concluding in November 2026; EnterpriseAM (2 Aug 2026) quotes IMF mission chief Amine Mati saying about $1.5bn (EFF) plus $800mn (RSF) remains for the final review in December and that "no formal talks on a new program have materialized yet." The prompt uses the IMF date.
- **Debt-service figures depend on definitions:** your "~$28bn" lines up with ADCB's $28.2bn estimate of FY2025/26 repayments and with the CBE's $28.3bn of actual service in the first nine months of FY2025/26.\[37\]\[38\] The CBE-projected public and publicly guaranteed schedule (via The Edge) shows $34.6bn for calendar 2026.\[39\] Ahram Online also labels the $164.8bn debt stock as both "end-June" and "end-March 2026";\[38\]\[57\] the end-March reading fits the CBE's quarterly cycle.
- **Hormuz traffic data conflict:** Kpler-based reporting in early October said flows had topped pre-war levels, while a tracker citing PortWatch showed very low transit counts on 11 October.\[58\]\[59\] This is why the prompt computes baselines from PortWatch history itself rather than hardcoding them.
- **Seeds come from secondary sources:** many seed values (CPI sub-indices, tourism, Suez revenue, LNG volumes, Decision 480 details) come from reputable Egyptian business press rather than the primary PDF. The prompt makes Phase 1 re-fetch them from primary sources or keep them flagged "secondary."
- **Oil budget sensitivities are rough:** the "EGP 3–4bn per $1/bbl" figures are commentators' estimates, not Ministry of Finance numbers,\[36\]\[60\] so the tool uses only the IMF's current-account rule of thumb. The gold-gap and other rule thresholds are configurable tool defaults, not an analyst consensus.
- **Some sources were not opened directly:** the FRED, EIA, ECB, Eurostat, World Bank and IMF SDMX series IDs listed are standard, but I did not open each one in this research pass. That is why Phase 0 verification is mandatory before any collector is written.

## Sources

1. [Moody's upgrades Egypt to B3, keeps positive outlook](https://en.amwalalghad.com/moodys-upgrades-egypt-to-b3-keeps-positive-outlook/)
2. [Daily Chokepoints Data - IMF PortWatch](https://portwatch.imf.org/datasets/imf-dataviz::daily-chokepoints-data)
3. [Suez Canal revenue rises 23% to \$4.6 billion in FY 2025/26: Chairman - Urban & Transport - Egypt - Ahram Online](https://english.ahram.org.eg/NewsContent/1/1235/571808/Egypt/Urban--Transport/Suez-Canal-revenue-rises--to--billion-in-FY--Chair.aspx)
4. [Egypt’s foreign reserves rise to \$57.35 bln in September: CBE](https://sis.gov.eg/en/media-center/news/egypt-s-foreign-reserves-rise-to-5735-bln-in-september-cbe/)
5. [Record remittances buffer Egypt against rising FY 2025/26 imports](https://manassa.news/en/news/34376)
6. [Geopolitical Risk (GPR) Index](https://www.matteoiacoviello.com/gpr.htm)
7. [Data Sources - gdelt-py](https://rbozydar.github.io/py-gdelt/getting-started/data-sources/)
8. [ACLED Alternative? Free Recent Event Data Linked to Satellite Imagery](https://offnadir-delta.com/acled-alternative)
9. [Arab News](https://www.arabnews.com/finance/moodys-upgrades-egypts-rating-to-b3-maintains-positive-outlook-3006980)
10. [S&P affirmed Egypt’s sovereign credit at B/B and Fitch Ratings at B, both with a stable outlook - EnterpriseAM Egypt](https://enterpriseam.com/egypt/2026/10/11/sp-affirmed-egypts-sovereign-credit-at-b-b-and-fitch-ratings-at-b-both-with-a-stable-outlook/)
11. [The EDA rewrites its drug-pricing rulebook around costs, competition, and localization - EnterpriseAM Egypt](https://enterpriseam.com/egypt/2026/09/27/the-eda-rewrites-its-drug-pricing-rulebook-around-costs-competition-and-localization/)
12. [Egypt: Medicine prices rise whenever the dollar rises](https://zawia3.com/en/medicine-pricing-egypt-480/)
13. [Meeting calendars and information](https://federalreserve.gov/monetarypolicy/fomccalendars.htm)
14. [Egypt's Rate Committee Meets on 20 August With Inflation Rising in Line With the Bank's Third-Quarter Forecast - The Edge for Economic Consultancy](https://edgeconsultancykw.com/egypt-mpc-preview-20-august-2026/)
15. [Egypt’s Reserves Hit Record US\$57.35 Billion](https://www.riotimesonline.com/egypt-foreign-reserves-record-september-2026)
16. [BREAKING: Egypt keeps fuel prices unchanged through December 2026 - Energy - Business - Ahram Online](https://english.ahram.org.eg/UI/Front/Inner.aspx?NewsContentID=580080)
17. [Gold prices rise by EGP 95 in one week](https://www.dailynewsegypt.com/2026/10/17/gold-prices-rise-by-egp-95-in-one-week/)
18. [Gold Price in Egypt Today](https://banklive.net/en/gold-price-today-in-egypt)
19. [Global Gold Gains 1.3% in a Week](https://see.news/global-gold-gains-13-in-a-week-as-egyptian-prices-shift-from-a-premium-to-a-discount)
20. [Query GDELT V2 Full Text API — ft\_v2\_api • gdeltr2 - ASBC LLC](https://asbcllc.com/gdeltr2/reference/ft_v2_api.html)
21. [toolkit/gitbook/tools/acled/README.md at main · bellingcat/toolkit · GitHub](https://github.com/bellingcat/toolkit/blob/main/gitbook/tools/acled/README.md)
22. [FAQ: ACLED’s new data structure, terms, and platforms](https://acleddata.com/faq-codebook-tools)
23. [© 2026 S&P Global S&P Global Egypt PMI® News Release](https://www.pmi.spglobal.com/Public/Home/PressRelease/1a8765e159c14fe19b3f9a72434c1058)
24. [Egypt's annual urban inflation falls to 13.9% in September — TradingView News](https://www.tradingview.com/news/reuters.com,2026:newsml_APNAQ9I5E:0-egypt-s-annual-urban-inflation-falls-to-13-9-in-september/)
25. [Egypt Urban Inflation Eases to 13.9% in September](https://www.riotimesonline.com/egypt-urban-inflation-13-9-percent-september-2026/)
26. [Egypt’s annual urban inflation eases to 13.9% in September](https://www.dailynewsegypt.com/2026/10/10/egypts-annual-urban-inflation-eases-to-13-9-in-september/)
27. [Central Bank of Egypt](https://en.wikipedia.org/wiki/Central_Bank_of_Egypt)
28. [Urban inflation eased to 13.9% in September, even as monthly prices continue to pick up - EnterpriseAM Egypt](https://enterpriseam.com/egypt/2026/10/11/urban-inflation-eased-to-13-9-in-september-even-as-monthly-prices-continue-to-pick-up/)
29. [18 MONETARY POLICY REPORT](https://www.cbe.org.eg/-/media/project/cbe/listing/publication/monetary-policy-report/2025/monetary-policy-report---mpr-q4-2025.pdf)
30. [ZAWYA: Egypt’s net international reserves reach \$57.35bln end-September: CBE — TradingView News](https://www.tradingview.com/news/reuters.com,2026-10-07:newsml_Zaw71sKwF:0-zawya-egypt-s-net-international-reserves-reach-57-35bln-end-september-cbe/)
31. [Home](https://www.cbe.org.eg/en/?author=2)
32. [Egypt's annual urban inflation eases to 13.9% in September 2026- Business Today](https://www.businesstodayegypt.com/Article/1/7983/Egypt-s-annual-urban-inflation-eases-to-13-9-in)
33. [Central Bank of Egypt](https://www.cbe.org.eg/en/)
34. [Despite Middle East war, Egypt remittances hit record \$33.9bn](https://www.newarab.com/news/despite-middle-east-war-egypt-remittances-hit-record-339bn)
35. [IDSC: Egypt tourism revenues, arrivals rise in 2026 amid regional tensions - Egypt Independent](https://www.egyptindependent.com/idsc-egypt-tourism-revenues-arrivals-rise-in-2026-amid-regional-tensions/)
36. [Egypt Hit By Higher Oil Prices And Rising Borrowing Costs: Report](https://see.news/egypt-hit-by-higher-oil-prices-rising-borrowing-costs-report)
37. [Egypt turns to short-term borrowing as debt piles up](https://www.agbi.com/analysis/economy/2025/11/egypt-turns-to-short-term-borrowing-as-debt-piles-up/)
38. [Infograph| Egypt’s external debt rises to \$164.8 bln at end-1Q 2026 - Economy - Business - Ahram Online](https://english.ahram.org.eg/NewsContentP/3/578015/Business/Infograph%7C-Egypt%E2%80%99s-external-debt-rises-to--bln-at-.aspx)
39. [Egypt’s External Debt Ratio Falls to 40.3 Percent of GDP, Reaching the Government Target Six Months Early - The Edge](https://edgeconsultancykw.com/egypt-external-debt-december-2025/)
40. [Fitch affirms Egypt’s ‘B’ rating with stable outlook](https://en.amwalalghad.com/fitch-affirms-egypts-b-rating-with-stable-outlook/)
41. [Moody’s upgrades Egypt by a notch as structural reforms bolster economic resilience](https://english.alarabiya.net/amp/business/economy/2026/10/17/moody-s-upgrades-egypt-by-a-notch-as-structural-reforms-bolster-economic-resilience)
42. [Egypt Non-Oil Private Sector PMI](https://tradingeconomics.com/egypt/manufacturing-pmi)
43. [Egypt (September 8th 2026) - MENA Market Lab](https://www.smartkarma.com/insights/egypt-september-8th-2026)
44. [How Egypt powers itself today - EnterpriseAM Egypt](https://enterpriseam.com/egypt/power-trip/how-egypt-powers-itself-today/)
45. [Egypt’s Strategic Pivot: Balancing Energy Security and Aviation Growth](https://see.news/egypts-strategic-pivot-balancing-energy-security-and-aviation-growth)
46. [Egypt’s War Math: Balancing Energy Supply and Cost](https://egyptoil-gas.com/features/egypts-war-math-balancing-energy-supply-and-cost/)
47. [Egypt Boosts Energy Import Budget by 37% to \$5.5 Billion for FY 2026/27 - The Middle East Observer](https://meobserver.org/energy/2026/05/12/egypt-boosts-energy-import-budget-by-37-to-5-5-billion-for-fy-2026-27/)
48. [Egypt Keeps Fuel Prices Steady for Q3 2026 Despite Global Oil Market Volatility](https://egyptoil-gas.com/news/egypt-keeps-fuel-prices-unchanged-for-q3-2026/)
49. [Egypt Keeps Gasoline and Diesel Prices Unchanged After Repeated Increases](https://see.news/egypt-keeps-gasoline-and-diesel-prices-unchanged-after-repeated-increases)
50. [Egypt Fuel Prices Today: Petrol, Diesel Rates on October 15](https://see.news/egypt-fuel-prices-today-petrol-diesel-rates-on-october-15)
51. [Brent oil - Price - Chart - Historical Data - News](https://tradingeconomics.com/commodity/brent-crude-oil)
52. [Egypt’s annual inflation rises to 12.8% in Sept - CAPMAS](https://en.amwalalghad.com/egypts-annual-inflation-rises-to-12-8-in-sept-capmas/)
53. [Egypt’s \$75 Oil Assumption Faces a \$100 Reality - The Middle East Observer](https://meobserver.news/energy/2026/10/08/egypts-75-oil-assumption-faces-a-100-reality/)
54. [Egypt Current Account Deficit Hits US\$22.5 Billion](https://www.riotimesonline.com/egypt-current-account-deficit-2026/)
55. [IMF Executive Board Completes the Fifth and Sixth Reviews Under the Extended Arrangement Under the Extended Fund Facility and First Review Under the Resilience and Sustainability Arrangement for Egypt](https://www.imf.org/en/news/articles/2026/02/26/pr-26064-egypt-imf-completes-5th-and-6th-revs-under-ext-arrange-under-eff-and-1st-rev-under-rsa)
56. [Fitch affirms Egypt at ’B’ with stable outlook as foreign buffers hold By Investing.com](https://www.investing.com/news/world-news/fitch-affirms-egypt-at-b-with-stable-outlook-as-foreign-buffers-hold-4939499)
57. [Egypt external debt rises 5.2% to \$164.8 bln at end-June 2026: CBE - Economy - Business - Ahram Online](https://english.ahram.org.eg/UI/Front/Inner.aspx?NewsContentID=574332)
58. [Strait of Hormuz Status: October 18, 2026](https://straits.live/briefs/2026-10-18)
59. [Oil Prices Fall as Reports Say Hormuz Crude Flows Top Pre-War Levels](https://oilprice.com/Latest-Energy-News/World-News/Oil-Prices-Fall-as-Hormuz-Crude-Flows-Top-Pre-War-Levels.html)
60. [How Oil Prices Increase Could Impact Egypt](https://see.news/how-oil-prices-increase-could-impact-egypt)
