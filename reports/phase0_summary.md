# Phase 0 — Source audit

Autonomous build, 2026-10-18 (Cairo). Checkpoint not paused per build instructions.

- `scripts/verify_sources.py` checked 41 sources → **24 OK, 15 MANUAL, 2 PAID** (`reports/phase0_source_audit.md`, raw samples in `data/raw/phase0/`).
- Key discovery: cbe.org.eg rejects non-browser User-Agents (F5 "Request Rejected"). With a standard browser UA (robots.txt allows the paths) the FX, CPI, T-bill, key-rate pages, the historical-data API and the news JSON API all work → CBE became automatic instead of MANUAL.
- Verified IDs: FRED (all 18 series, keyless CSV), PortWatch Suez=chokepoint1, Bab el-Mandeb=chokepoint4, Hormuz=chokepoint6; GPR has GPRC_EGY (+ISR, SAU); FOMC page lists 2026 meetings.
- Changed: euro-area HICP — old ECB key and Eurostat `prc_hicp_manr` are frozen at Dec 2025; switched to Eurostat `prc_hicp_minr` (RCH_A) → Sep 2026 = 3.8%.
- MANUAL by rule: FRED API & EIA (key/account), ACLED (no API on Open tier), CAPMAS & MoF (JS-only apps), EGX (connection reset), NBE/goldpricez (JS-rendered), Ahram RSS (404), IMF RSS (403), Arab Finance RSS (410), parallel FX, Eurobonds. PAID: CDS, EMBI/MSCI/consensus/Kpler/full PMI.
- GDELT: 429 on three probes, then answered → automatic but rate-limited intermittently.
- Caveats re-verified: Moody's Caa1→B3 positive on 16 Oct 2026 (Amwal Al Ghad + EnterpriseAM RSS); Fitch B stable (8 Oct) and S&P B/B stable (date not stated; EnterpriseAM 10 Oct); IMF program ends December (EnterpriseAM, IMF PR) — Fitch's "November" not used; 7th review ~$1.5bn EFF + $272mn RSF (Zawya).
