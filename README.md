# Egypt Macro Pulse

A local learning tool that collects, stores, links (cause → effect rules) and visualizes what drives
USD/EGP and Egypt's economy. **Not financial advice.** Spec: [SPEC.md](SPEC.md).

## Open the app

**Public (GitHub Pages):** https://ehabessam716-ui.github.io/egypt-macro-pulse/ — rebuilt by GitHub Actions
(`.github/workflows/pulse.yml`) on the same schedule; the database lives in the `state` release.
Run it on demand: GitHub → Actions → Pulse → *Run workflow*.

**Live layer (fully automatic, nothing to keep open):** `.github/workflows/live.yml` runs every 15 minutes on GitHub's
servers. It refreshes intraday market quotes (USD/EGP market, EGX30, Brent, world gold, dollar index, VIX, US 10Y,
wheat, EU gas, EM stocks — Yahoo, delayed), local 21K gold (banklive), today's CBE official rate and the latest
headlines, recomputes the live insights (gold-implied rate vs official, oil vs budget, EGX30 in dollars, risk mood) and
republishes the site. The page shows them in **Right now** and refreshes itself every minute. Intraday quotes are kept
out of the official daily record (`site/data/live.js` only). Manually: `pulse live`.

**On this PC:**

**http://localhost:8765** — starts automatically when you log in to Windows (task `\EgyptMacroPulse\server_at_logon`).
Manually: `.venv\Scripts\pulse serve --open`. Without the server you can also open `site/index.html` directly (no Update-now button).

- Pound Pressure gauge, sub-indices (click one to drill in), today's story, key numbers with sparklines
- Click any number → history chart (1M…All), source, definition, observations table, CSV download
- Every number has a **"What this means"** panel (EN/AR): what it is · what usually moves it · what happened (its change, plus
  related indicators, signals and events from the same period — shown as *possible reasons from the data, not proof*) ·
  what it may lead to. Texts live in `config/explain.yaml` (edit freely).
- **ⓘ Explain** switch in the header adds a one-line meaning + impact to every tile.
- Stock market: **EGX30** (Yahoo `^CASE30`, unofficial; history builds from 18 Oct 2026) and **EGX70 EWI** (MANUAL — EGX's site
  is behind an anti-bot challenge, so enter closes in `data/manual/manual_inputs.xlsx`).
- `Ctrl K` or `/` to search all 199 indicators · EN / ع switch (full right-to-left Arabic) · light / dark / auto theme
- Live: the page checks for new data every 60 s and updates in place (changed tiles glow); **Update now** runs a fresh collection
- Links: `?lang=ar`, `?theme=dark`, `#/signals`, `#/brief`, `#/d/fx`, `#/s/nir` (opens an indicator)

## One command

```powershell
.venv\Scripts\pulse run --job all        # collect everything → derive → rules → indices → brief → weekly → dashboard → Power BI
```

Scheduled jobs (Windows Task Scheduler, folder `\EgyptMacroPulse`, Africa/Cairo times):

| job | when | what |
|---|---|---|
| `daily` | 09:30 and 18:30 Sun–Thu | CBE (FX, rates, CPI, T-bills, press releases), Yahoo, Egypt gold, PMI, PortWatch, RSS, GDELT → full analysis + Arabic brief |
| `global` | 23:30 Mon–Fri | FRED, Yahoo, World Bank/IMF/Eurostat, PortWatch → analysis + dashboard |
| `weekly` | Thu 20:00 | press releases, PortWatch, FOMC check → weekly deep-dive + backtest |
| `gpr` | Mon 12:00 and the 2nd of each month | Caldara–Iacoviello GPR files |
| `calendar` | 07:00 daily | release calendar + `reports/alerts_next48h.md` |

Re-install the schedule: `.venv\Scripts\python scripts\install_schedule.py` (remove: `--remove`).
Tasks run as the logged-in user (no stored password), so they only fire while you are logged on;
missed runs start when the PC wakes (`StartWhenAvailable`).

## Where things are

| output | path |
|---|---|
| App (web) | http://localhost:8765 or `site/index.html` (code in `pulse/web/`) |
| Arabic daily brief | `briefs/YYYY-MM-DD.md` and `.html` |
| Weekly deep-dive | `reports/weekly/YYYY-MM-DD.md` |
| Power BI star schema | `exports/*.csv` (UTF-8 BOM) and `*.parquet` |
| Database | `data/pulse.db` (SQLite) · raw responses in `data/raw/` |
| Manual inputs (optional) | `data/manual/manual_inputs.xlsx` |
| Logs | `logs/pulse.log` |
| Source audit | `reports/phase0_source_audit.md` |

## Other commands

```
pulse doctor [--fix]        health check: DB integrity, stale series, failed sources, missing manual inputs, Arabic rule
pulse collect cbe_fx fred   run named collectors (add --backfill for full history)
pulse analyse               derive → rules → indices → brief → dashboard → export (no fetching)
pulse events queue          candidate events waiting for review
pulse events confirm <id>   promote a candidate (reject <id> deletes it)
pulse run --job daily --dry-run
```

## How it works

1. **Collect** (`pulse/collectors/`): free, keyless sources only. Every value is stored with source name, URL,
   observation date, release date and retrieval time; quality flag `official / secondary / unofficial / manual / derived`.
   Revisions become new vintages; disagreeing sources are both kept and flagged.
2. **Derive** (`pulse/derive.py`): real rates, gold-implied FX, FX momentum/volatility, oil gap, coverage ratios,
   chokepoint ratios vs the 2023 baseline, PMI-implied GDP, EDA repricing signal… only when every input exists.
3. **Rules** (`config/rules.yaml` + `pulse/rules.py`): 40 cause → effect rules with English and Egyptian-Arabic
   explanations; rules with missing inputs are reported as "not evaluable" rather than guessed.
4. **Indices** (`config/indices.yaml`): Pound Pressure Index (−100 relief … +100 pressure) with six weighted sub-indices,
   plus Inflation Pressure and Growth indices. Coverage below 60% greys the PPI out.
5. **Events** (`config/events_taxonomy.yaml`): decaying event scores. RSS + GDELT headlines create *candidates*;
   a candidate becomes *reported* only when ≥ 2 independent outlets report it within 48 hours. Candidates never move indices.

Manual data is optional: the workbook is pre-filled with the spec's seeds (quality `secondary`). Empty tabs only lower coverage.

## Tests

```
.venv\Scripts\python -m pytest
```
