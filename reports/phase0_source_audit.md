# Phase 0 — Source audit

Run: 2026-10-18 18:27 (Africa/Cairo). Status counts: **OK** 24, **MANUAL** 15, **PAID** 2

| source | status | HTTP | frequency observed | latest observation | notes |
|---|---|---|---|---|---|
| `cbe_fx_rates` CBE official exchange rates (+ historical-data API) | **OK** | 200 | — | — | robots: allowed; browser User-Agent required (firewall rejects tool UA) |
| `nbe_fx` National Bank of Egypt exchange rates (fallback) | **MANUAL** | — | — | — | JS-only single-page app; CBE page works so no fallback scraper is needed |
| `yahoo_markets` Yahoo Finance market proxies (unofficial) | **OK** | 200 | daily | EGP=X=2026-10-18 close=53.5; BZ=F=2026-10-16 close=109.9; CL=F=2026-10-16 close=99.02; GC=F=2026-10-16 close=4181; SI=F=2026-10-16 close=57.31; ZW=F=2026-10-16 close=660.5; TTF=F=2026-10-16 close=87.55; DX-Y.NYB=2026-10-16 close=101.8; EEM=2026-10-16 close=62.85 | UNOFFICIAL source (Yahoo) — quality_flag='unofficial' |
| `egx` Egyptian Exchange (foreign net flows bulletin) | **MANUAL** | — | — | — | connection reset for scripted clients in Phase 0; bulletin is an ASP.NET postback page — MANUAL |
| `fx_parallel` Parallel-market USD/EGP | **MANUAL** | — | — | — | no official or free programmatic source |
| `eurobonds` Egypt USD Eurobond yields | **MANUAL** | — | — | — | no free licensed feed; enter from press |
| `cds` Egypt 5Y CDS | **PAID** | — | — | — | Bloomberg/Refinitiv only; MANUAL weekly from press |
| `cbe_home` CBE homepage (key rates, CONIA) | **OK** | 200 | — | — | robots: allowed; browser User-Agent required (firewall rejects tool UA) |
| `cbe_mpc` CBE key rates / MPC schedule page | **OK** | 200 | — | — | robots: allowed; browser User-Agent required (firewall rejects tool UA); found 'Overnight Deposit Rate' |
| `cbe_cpi` CBE inflation rates page (headline/core m/m, y/y) | **OK** | 200 | — | — | robots: allowed; browser User-Agent required (firewall rejects tool UA); found 'Inflation for Last Month' |
| `cbe_news` CBE news listing JSON (NIR, remittances, MPC, CPI, BoP releases) | **OK** | 200 | 804 news items (paged JSON) | 2026-10-13 | latest NIR headline: Net International Reserves reached US$ 57,348.2 mn at the end of September 2026 (Provisional) |
| `cbe_bop` CBE balance-of-payments press-release PDFs | **OK** | 200 | — | — | browser User-Agent required (firewall rejects tool UA) |
| `cbe_auctions` CBE T-bill auctions (+ historical-data API) | **OK** | 200 | — | — | robots: allowed; browser User-Agent required (firewall rejects tool UA); found 'Weighted Avg. Yield' |
| `capmas` CAPMAS (CPI detail, trade, labour) | **MANUAL** | — | — | — | JS-only app ('You need to enable JavaScript'); headline/core CPI come from CBE instead |
| `mof` Ministry of Finance (financial monthly, debt) | **MANUAL** | — | — | — | JS-only app; no data in HTML |
| `sp_pmi` S&P Global PMI press releases (Egypt, Saudi, UAE headline) | **OK** | 200 | — | — | robots: allowed; found 'Egypt PMI'; robots.txt HTTP 404 (treated as allowed) |
| `portwatch_chokepoints` IMF PortWatch Daily Chokepoints Data | **OK** | 200 | daily | 2026-10-11 | ArcGIS item 3da2b9ca97684916b75c4013f95d18ab owner=IMF-portwatch_imf_dataviz title=Daily_Chokepoints_Data; fields: date, year, month, day, portid, portname, n_container, n_dry_bulk, n_general_cargo, n_roro, n_tanker, n_cargo, n_total, capacity_container, capacity_dry_bulk, capacity_general_cargo, capacity_roro, capacity_tanker, capacity_cargo, capacity, ObjectId; 28 chokepoints; matches: Bab el-Mandeb Strait=chokepoint4, Balabac Strait=chokepoint25, Bering Strait=chokepoint26, Bohai Strait=chokepoint17, Bosporus Strait=chokepoint3, Dover Strait=chokepoint9, Gibraltar Strait=chokepoint8, Kerch Strait=chokepoint28, Korea Strait=chokepoint12, Lombok Strait=chokepoint15, Luzon Strait=chokepoint14, Magellan Strait=chokepoint21, Makassar Strait=chokepoint20, Malacca Strait=chokepoint5, Mindoro Strait=chokepoint27, Ombai Strait=chokepoint16, Oresund Strait=chokepoint10, Strait of Hormuz=chokepoint6, Suez Canal=chokepoint1, Sunda Strait=chokepoint19, Taiwan Strait=chokepoint11, Torres Strait=chokepoint18, Tsugaru Strait=chokepoint13 |
| `gpr_monthly` Caldara–Iacoviello GPR monthly (incl. country indexes) | **OK** | 200 | monthly | 2026-09-01 | Egypt columns: GPRC_EGY, GPRHC_EGY; GPRC_EGY latest non-null: 2026-09-01; optional columns present: GPRC_ISR, GPRC_SAU |
| `gpr_daily` Caldara–Iacoviello GPR daily (recent) | **OK** | 200 | daily | 2026-10-13 | optional columns present: GPRD_ACT, GPRD_THREAT |
| `gdelt_doc` GDELT DOC 2.0 API | **OK** | 200 | daily | 2026-10-18 13:00:00+00:00 | rolling ~3-month window; keep >=6s between calls |
| `acled` ACLED conflict events | **MANUAL** | — | — | — | Open tier (personal email) has no API; account creation not allowed by policy |
| `fred_csv` FRED (keyless graph CSV) | **OK** | 200 | — | DFF=2026-10-15 (daily, last=3.88); FEDFUNDS=2026-09-01 (monthly, last=3.75); DGS10=2026-10-15 (daily, last=5.1); DGS2=2026-10-15 (daily, last=4.77); T10YIE=2026-10-16 (daily, last=2.35); CPIAUCSL=2026-09-01 (monthly, last=336.298); CPILFESL=2026-09-01 (monthly, last=338.896); PAYEMS=2026-09-01 (monthly, last=159044); UNRATE=2026-09-01 (monthly, last=4.2); VIXCLS=2026-10-15 (daily, last=16.46); DTWEXBGS=2026-10-09 (daily, last=121.6023); DEXUSEU=2026-10-09 (daily, last=1.1193); DCOILBRENTEU=2026-10-14 (daily, last=126.55); DCOILWTICO=2026-10-14 (daily, last=101.91); DHHNGSP=2026-10-14 (daily, last=3.22); PNGASEUUSDM=2026-07-01 (monthly, last=17.93); PWHEAMTUSDM=2026-07-01 (monthly, last=228.73884495); BAMLEMCBPIOAS=2026-10-15 (daily, last=1.59) | keyless fredgraph CSV works without an API key; API key only needed for metadata/vintages (ALFRED) |
| `fred_api` FRED REST API | **MANUAL** | — | — | — | needs an API key (account) — not used; keyless fredgraph CSV covers every series |
| `eia_api` EIA Open Data API v2 | **MANUAL** | — | — | — | needs an API key — skipped by policy; Brent/WTI come from FRED (EIA data) with Yahoo futures fallback |
| `fomc_calendar` Fed FOMC calendar | **OK** | 200 | — | — | found '2026 FOMC Meetings' |
| `worldbank_api` World Bank API (Egypt GDP growth) | **OK** | 200 | — | 2025 value=4.39 | — |
| `imf_datamapper` IMF DataMapper API (WEO Egypt) | **OK** | 200 | — | years 1980–2031 (includes WEO projections) | — |
| `ecb_hicp` ECB Data Portal (euro-area HICP y/y, old key) | **MANUAL** | 200 | — | 2025-12 value=1.9 | reachable=MOVED; policy keeps it MANUAL; STALE: latest period is 290 days old (> 75) — series likely discontinued or renamed; series key frozen at 2025-12 (COICOP-2018 switch); replaced by Eurostat prc_hicp_minr |
| `eurostat_hicp` Eurostat API (euro-area HICP y/y, COICOP 2018) | **OK** | 200 | — | 2026-09 value=3.8 | — |
| `gold_banklive` banklive.net gold price in Egypt | **OK** | 200 | — | — | robots: allowed |
| `gold_isagha` iSagha gold prices (fallback, 24K only) | **OK** | 200 | — | — | robots: allowed |
| `gold_goldpricez` goldpricez Egypt gram price | **MANUAL** | — | — | — | prices rendered by JavaScript; banklive + iSagha are enough |
| `rss_dne` Daily News Egypt RSS | **OK** | 200 | 10 items in feed | 2026-10-18T18:06+03:00 | — |
| `rss_egypt_independent` Egypt Independent RSS | **OK** | 200 | 10 items in feed | 2026-10-18T15:36+03:00 | — |
| `rss_mada` Mada Masr RSS | **OK** | 200 | 10 items in feed | 2026-10-17T17:51+03:00 | — |
| `rss_enterprise` EnterpriseAM Egypt RSS | **OK** | 200 | 10 items in feed | 2026-10-18T00:00+03:00 | — |
| `rss_ahram` Ahram Online RSS (business) | **MANUAL** | — | — | — | feed URL returns 404 (also tried /rss/3.aspx, /rss.aspx); no RSS link on the homepage |
| `rss_imf` IMF news RSS | **MANUAL** | — | — | — | HTTP 403 Access Denied (Akamai) for scripted clients |
| `rss_arabfinance` Arab Finance RSS | **MANUAL** | — | — | — | HTTP 410 Gone |
| `manual_events` Ratings, IMF, fuel committee, EDA, Gulf deals, LNG, load-shedding, Suez revenue, tourism | **MANUAL** | — | — | — | event-type facts; seeded from the spec, then auto-candidates from RSS (2-outlet rule) |
| `paid_block` EMBI, MSCI EM index, consensus, Kpler, full PMI sub-indices | **PAID** | — | — | — | paid terminals/licences; free proxies used (BAMLEMCBPIOAS, EEM, PMI headline) |

## Samples (first 200 chars)

- `cbe_fx_rates` (text/html; charset=utf-8, last-modified —): Exchange Rates Banner Search Careers Contact Us Investor Relations Consumer Protection عربى عربى Explore Financial Stability Overview and Objectives Macroprudential Policy On Site Supervision Off Site
- `nbe_fx` (—, last-modified —): —
- `yahoo_markets` (—, last-modified —): —
- `egx` (—, last-modified —): —
- `fx_parallel` (—, last-modified —): —
- `eurobonds` (—, last-modified —): —
- `cds` (—, last-modified —): —
- `cbe_home` (text/html; charset=utf-8, last-modified —): Home Banner Search Careers Contact Us Investor Relations Consumer Protection عربى عربى Explore Financial Stability Overview and Objectives Macroprudential Policy On Site Supervision Off Site Supervisi
- `cbe_mpc` (text/html; charset=utf-8, last-modified —): MPC Decisions Banner Search Careers Contact Us Investor Relations Consumer Protection عربى عربى Explore Financial Stability Overview and Objectives Macroprudential Policy On Site Supervision Off Site 
- `cbe_cpi` (text/html; charset=utf-8, last-modified —): Inflation Rates Banner Search Careers Contact Us Investor Relations Consumer Protection عربى عربى Explore Financial Stability Overview and Objectives Macroprudential Policy On Site Supervision Off Sit
- `cbe_news` (application/json; charset=utf-8, last-modified —): Remittances from Egyptians Working Abroad Record USD 33.9 Billion During the First Eight Months of 2026
- `cbe_bop` (text/html; charset=utf-8, last-modified —): News Banner Search Careers Contact Us Investor Relations Consumer Protection عربى عربى Explore Financial Stability Overview and Objectives Macroprudential Policy On Site Supervision Off Site Supervisi
- `cbe_auctions` (text/html; charset=utf-8, last-modified —): EGP T-Bills Banner Search Careers Contact Us Investor Relations Consumer Protection عربى عربى Explore Financial Stability Overview and Objectives Macroprudential Policy On Site Supervision Off Site Su
- `capmas` (—, last-modified —): —
- `mof` (—, last-modified —): —
- `sp_pmi` (text/html; charset=utf-8, last-modified Sun, 18 Oct 2026 15:25:16 GMT): PMI Releases &nbsp; Language العربية English Italiano Português ไทย Čeština Español 日本語 Pусский Deutsch Français Nederlands Türkçe ΕΛΛΗΝΙΚΑ Bahasa Indonesia Polski Tiếng Việt Join a panel MEMBERS ABOU
- `portwatch_chokepoints` (—, last-modified —): date=2026-10-11, year=2026, month=10, day=11, portid=chokepoint1, portname=Suez Canal, n_container=13, n_dry_bulk=5, n_general_cargo=4, n_roro=1
- `gpr_monthly` (application/vnd.ms-excel, last-modified Tue, 13 Oct 2026 15:45:32 GMT): 1521 rows, 115 columns; date column 'month'
- `gpr_daily` (application/vnd.ms-excel, last-modified Tue, 13 Oct 2026 15:45:32 GMT): 15261 rows, 11 columns; date column 'DAY'
- `gdelt_doc` (application/json; charset=utf-8, last-modified —): Average Tone: last value -3.3733
- `acled` (—, last-modified —): —
- `fred_csv` (—, last-modified —): DFF=2026-10-15 (daily, last=3.88)
- `fred_api` (—, last-modified —): —
- `eia_api` (—, last-modified —): —
- `fomc_calendar` (text/html, last-modified Wed, 07 Oct 2026 18:00:37 GMT): The Fed - Meeting calendars and information Skip to main content An official website of the United States Government Here&#x27;s how you know Official websites use .gov A .gov website belongs to an of
- `worldbank_api` (application/json;charset=utf-8, last-modified Sat, 17 Oct 2026 15:55:44 GMT): [{"page": 1, "pages": 14, "per_page": 5, "total": 66, "sourceid": "2", "lastupdated": "2026-10-08"}, [{"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth (annual %)"}, "country": {"id": "EG
- `imf_datamapper` (application/json, last-modified —): {"values": {"NGDP_RPCH": {"SDN": {"1980": 2.5, "1981": 6.3, "1982": 4.1, "1983": -1.5, "1984": -5.6, "1985": -0.6, "1986": 9.9, "1987": 6.5, "1988": 4.3, "1989": 1.4, "1990": 0.8, "1991": 7, "1992": 5
- `ecb_hicp` (application/vnd.sdmx.data+json;version=1.0.0-wd, last-modified Mon, 19 Jan 2026 10:05:23 GMT): {"header": {"id": "58d26d80-3abd-4210-8ad3-b8a5aa8efd55", "test": false, "prepared": "2026-10-14T00:30:07.484+02:00", "sender": {"id": "ECB"}}, "dataSets": [{"action": "Replace", "validFrom": "2026-10
- `eurostat_hicp` (application/json, last-modified —): {"version": "2.0", "class": "dataset", "label": "Harmonised index of consumer prices (HICP) - ECOICOP ver.2 - indices and rates of change, monthly data", "source": "ESTAT", "updated": "2026-10-16T23:0
- `gold_banklive` (text/html; charset=UTF-8, last-modified —): Gold Price in Egypt Today \| BankLive Egypt Home Exchange Rates in Egyptian Banks Global Currency Rates Currency Converter Fuel and metal prices Gold Price Silver Price Gasoline prices Most traded curr
- `gold_isagha` (text/html; charset=utf-8, last-modified —): سعر الذهب اليوم في مصر لحظة بلحظة \| iSagha توصيل مؤمَّن لكل المحافظات فاتورة ضريبية لكل طلب استلام من الفرع خلال 24 ساعة +20 106 008 5957 بحث المتجر أسعار اليوم الحاسبات حاسبة الذهب والفضة حاسبة الزكا
- `gold_goldpricez` (—, last-modified —): —
- `rss_dne` (application/rss+xml; charset=UTF-8, last-modified Sun, 18 Oct 2026 15:06:18 GMT): Egypt’s financial regulator approves Banque Du Caire IPO prospectus for 30% stake worth up to EGP 24.25bn
- `rss_egypt_independent` (application/rss+xml; charset=UTF-8, last-modified Sun, 18 Oct 2026 12:36:13 GMT): Even LinkedIn is getting tired of your AI-written posts
- `rss_mada` (application/rss+xml; charset=UTF-8, last-modified Sun, 18 Oct 2026 10:50:59 GMT): Govt scrambles to solve fuel crisis without clear end in sight, divided on fava bean import ban; Quintet tries to balance competing political initiatives; RSF continues Blue Nile push; Military sets s
- `rss_enterprise` (application/rss+xml; charset=UTF-8, last-modified Sun, 18 Oct 2026 13:29:26 GMT): Moody’s raises Egypt’s local and foreign currency ratings to B3 and kept a positive outlook
- `rss_ahram` (—, last-modified —): —
- `rss_imf` (—, last-modified —): —
- `rss_arabfinance` (—, last-modified —): —
- `manual_events` (—, last-modified —): —
- `paid_block` (—, last-modified —): —
