# Egypt Macro Pulse — build summary (2026-10-18)

All phases 0–8 are complete. Phase notes: `reports/phase0_summary.md` … `phase8_summary.md`.
41 pytest tests pass; `pulse doctor` reports 0 critical issues; 6 Windows scheduled tasks are registered and a
scheduler-launched daily run finished with result 0.

## What works automatically

| source | what | when it updates |
|---|---|---|
| Central Bank of Egypt (cbe.org.eg) | official USD/EGP buy/sell (history from Jan 2023), key rates, CPI headline/core, T-bill auctions, NIR (from Dec 2014), remittances, MPC decisions + statement tone, GDP from MPC text, BoP fiscal-year PDFs | daily runs 09:30 / 18:30 Sun–Thu |
| FRED keyless CSV | Brent/WTI spot (EIA), Henry Hub, TTF, wheat, US rates, CPI, jobs, VIX, broad dollar, EM spread proxy, EUR/USD | 23:30 Mon–Fri |
| Yahoo Finance (unofficial) | EGP=X, Brent/WTI/TTF/wheat futures, gold, silver, DXY, EEM | daily + global runs |
| IMF PortWatch | Suez, Bab el-Mandeb and Hormuz daily transits (source updates on Tuesdays) | daily + global runs |
| Caldara–Iacoviello GPR | global/threats/acts, Egypt/Israel/Saudi (monthly), daily GPR | Mon 12:00 and the 2nd |
| S&P Global PMI press PDFs | Egypt, Saudi, UAE headline PMI | daily runs |
| banklive / iSagha | Egypt gold 21K/24K/pound + spot XAU at the same timestamp | daily runs |
| World Bank, IMF DataMapper, Eurostat | GDP, WEO forecasts, euro-area HICP | global runs |
| RSS (DNE, Egypt Independent, Mada Masr, EnterpriseAM) + CBE news + GDELT | headlines → event candidates; GDELT tone/volume | daily runs |
| Fed FOMC page | meeting dates check | weekly + calendar runs |

The release calendar and 48-hour alerts (`reports/alerts_next48h.md`) refresh daily at 07:00.
The weekly deep-dive and the 2-year backtest run Thursday 20:00.

## MANUAL / PAID series and why

The tool runs without them; they only lower coverage. Seeds from the spec are already in
`data/manual/manual_inputs.xlsx` (quality 'secondary', each with a source URL).
- **CAPMAS detail** (nationwide/food/health CPI, unemployment) and **MoF** (budget, debt, interest/revenue): JavaScript-only sites.
- **EGX foreign flows**: the site resets scripted connections.
- **Parallel FX, Eurobond yields, external debt stock/service, NIR gold/FX/SDR split, fuel prices, tourism arrivals, SCA Suez revenue, LNG volumes**: no free programmatic source.
- **ACLED**: the Open tier has no API. **FRED API / EIA**: need keys (not used; FRED CSV covers Brent/WTI).
- **CDS, EMBI, MSCI index, consensus, Kpler, full PMI**: paid.
- **Dead feeds**: Ahram Online RSS (404), IMF RSS (403), Arab Finance RSS (410).

**Coverage now:** Pound Pressure Index coverage **82%** (threshold 60%). 161 of 199 series have data. 30 MANUAL series are empty.
Seeds: 18 confirmed against primary sources, 0 conflicts, 30 secondary-only (`reports/seed_verification.md`).

## Today's reading (18 Oct 2026)

**PPI +11.8 (mild pressure).**
- Pressure: oil ≈ $52/bbl above the $75 budget assumption; current-account deficit +46%; Suez traffic at 57% and Hormuz at 4% of the 2023 average.
- Relief: record NIR of $57.35bn (6.3 months of imports), remittances +21.7%, a real rate of +5.1 pp, and the Moody's upgrade to B3.
- Watch: the IMF EFF ends in 58 days with no successor announced.

## The app (added after the first build)

- **Link:** http://localhost:8765 (served by `pulse serve`, auto-started at Windows logon; binds to this PC only).
- **Identity:** "Pulse · نبض" — pyramid + heartbeat logo, Nile-teal / sand-gold / papyrus palette, IBM Plex Sans + IBM Plex Sans Arabic.
- **Features:** gauge, drill-down sub-indices, sparkline tiles, indicator drawer (history, source, CSV), Ctrl K search, signals with "learn the concept", events with decay, calendar countdowns, Arabic brief in-app, data & sources page with the backtest.
- **Bilingual:** EN / ع switch with full right-to-left layout; numbers and dates kept left-to-right.
- **Live:** polls every 60 s and updates in place; the **Update now** button runs `pulse run --job daily` through the server.
- **No console windows:** scheduled jobs and the server run with `pythonw`.

## How to use

- **App:** http://localhost:8765 (or open `site/index.html`).
- **Daily Arabic brief:** `briefs/YYYY-MM-DD.md` (+ `.html`).
- **Weekly report:** `reports/weekly/`.
- **Power BI:** `exports/*.csv` / `*.parquet`.
- **Run everything manually (one command):** `.venv\Scripts\pulse run --job all`
- **Health check:** `.venv\Scripts\pulse doctor`.
- **Review event candidates:** `pulse events queue`, `pulse events confirm <id>`.

## Known limitations / what failed

- **GDELT** rate-limits this IP (HTTP 429) on most runs. Each run fetches the stalest query first, so the series fill in gradually. Today: Egypt-economy tone + one more series.
- **Memory**: this PC (8 GB) runs low on memory when several large apps are open. The first scheduled run hit `MemoryError` in two steps (other steps still completed). The tool now caches data compactly and a repeat scheduled run was clean, but very low free memory can still make a step fail. The step is then skipped and logged, and the next run catches up.
- **Scheduled tasks** run only while you are logged on (no password stored). Missed runs start when the PC wakes.
- **CBE** blocks non-browser User-Agents, so the tool sends a standard browser UA (robots.txt allows these pages). If CBE changes its firewall or page layout, these collectors fail and are logged.
- **Not parsed**: quarterly BoP releases (only fiscal-year ones). CBE's CPI history form doesn't work, so CPI history comes from press releases (since 2023).
- **Brent**: dated spot (FRED, $126.55 on 14 Oct) and front-month futures ($109.9 on 16 Oct) diverge sharply. Both are shown; the rules use the spot price per the spec.
- **GDP growth** comes only from MPC statements (2 quarters). **The remittances 12-month sum** needs 12 consecutive monthly prints (10 so far).
- **Backtest**: release dates are estimated where unknown, so it is approximate point-in-time and for learning only.
- **Event candidates** use keywords and include some false positives (e.g. Sudan/RSF flagged as regional war). They never count until confirmed or reported by 2 independent outlets within 48 h.
