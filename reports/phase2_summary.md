# Phase 2 — External & fiscal

Autonomous build, 2026-10-18 (Cairo). Checkpoint not paused per build instructions.

- PortWatch daily transits/capacity for Suez, Bab el-Mandeb, Hormuz since 2022; 2023 baseline computed from that history. Latest 7-day ratios: Suez 0.57, Bab el-Mandeb ~0.38, Hormuz 0.04 (11 Oct).
- BoP FY press-release PDF parser (pdfplumber): CA −22.5bn (vs −15.4), overall +2.8, remittances 47.3, tourism 18.4, Suez receipts 4.4, FDI 18.0, portfolio 4.2, oil/non-oil trade. Quarterly BoP releases are detected but not parsed (limitation).
- T-bill auctions (91/182/273/1-year) with yield, bid-to-cover, accepted/offered — ~3 years.
- Remittance press releases → monthly value, y/y and calendar YTD.
- `data/manual/manual_inputs.xlsx`: 56 tabs, 48 seed rows (quality 'secondary', each with source URL) + 7 seeded events; validated import (rows without date/value/URL rejected → `reports/manual_import_rejects.md`).
