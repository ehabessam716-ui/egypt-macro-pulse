# Phase 8 — Scheduling, tests, docs

Autonomous build, 2026-10-18 (Cairo). Checkpoint not paused per build instructions.

- 41 pytest tests pass (formulas incl. 16 Oct gold sanity case, rules on fixtures, index bounds/coverage, decay, Arabic-no-Latin, export schema, calendar time zones, parsers, 2-outlet rule).
- `pulse doctor`: 0 critical; warnings are rate-limited GDELT series and MANUAL gaps only.
- Windows Task Scheduler: 6 tasks under `\EgyptMacroPulse` (XML templates in `ops/windows/`, cron template `ops/cron.txt`), venv Python with absolute paths, Cairo times (machine is on Egypt Standard Time).
- README.md + README_ar.md.
