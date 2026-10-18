# Phase 5 — Rules, indices, backtest

Autonomous build, 2026-10-18 (Cairo). Checkpoint not paused per build instructions.

- 47 rules (`config/rules.yaml`, `pulse/rules.py`); today: 35 evaluable, **11 fired** — EC01 oil gap (+, strong), EC02 deferred fuel pass-through, EC05 Hormuz, EX02 Suez weak, EX05 CA deficit +46%, FD03 IMF EFF ends in 58 days (watch), RE01 PMI <50 for 3 months; relief: EX01 remittances +21.7%, EX06 record NIR (6.3 months of imports), MO01 real rate +5.1 pp, FD04 Moody's upgrade.
- Not evaluable (missing MANUAL/PAID inputs): consensus, CDS/Eurobond, EGX flows, credit, interest/revenue, etc.
- **PPI +11.8, coverage 82%**: commodities +78, geopolitical +37, global +2, monetary −4, external −8, fiscal −20. Inflation index +17 (80%), Growth index −24 (25%).
- Backtest: 104 weekly point-in-time PPI values (range −33 to +21, coverage 72–82%) on `site/backtest.html`.
