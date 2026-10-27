# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

## Sales forecast

- **Script:** [`train_sales_forecast.py`](./train_sales_forecast.py)
- **Series:** `data/raw/brasaland_sales.csv` (consolidated monthly revenue, 2016–2025)
- **Brief:** [`docs/forecasting/CONTEXT-company.md`](../docs/forecasting/CONTEXT-company.md)
- **Run:** `uv run python scripts/train_sales_forecast.py`
- Training is 2016–2023. The check is 2024–2025. The chart is `data/eval/sales_forecast_test.png`. Metric definitions are in [`docs/forecasting/README.md`](../docs/forecasting/README.md).

## Nightly telemetry export

- **Script:** [`nightly_export.py`](./nightly_export.py)
- **Status table:** `job_runs`, written by [`services/job_runner.py`](../services/job_runner.py). This is the nightly orchestration log. `reporting.weekly_performance_run` stays the Milestone 6 pipeline log.
- **Backup CSV:** `data/raw/telemetry_YYYY-MM-DD.csv`, created only when that file is absent. The weekly pipeline reads `telemetry_events`, not this file. The CSV is gitignored because it can contain `user_id`.
- **Trigger:** crontab at 02:00 UTC, expression `0 2 * * *`. The line is in [`nightly-export.cron`](./nightly-export.cron). The API process does not start this script.

```bash
services/api/.venv/bin/python scripts/nightly_export.py
TARGET_DATE=2026-09-28 services/api/.venv/bin/python scripts/nightly_export.py
```

`TARGET_DATE` is a UTC calendar day (`YYYY-MM-DD`). When it is unset, the script uses yesterday in UTC.

## Company File Analyzer — required layout

Submission structure for this assignment (Brasaland uses `incidents-brasaland.csv` where the brief says `incidents-COMPANY.csv`):

```text
scripts/
  analyze.py
  incidents-brasaland.csv

services/
  api/

uis/
  web/
```

## Incident Report Processor (Phase 1)

- **Script:** [`analyze.py`](./analyze.py)
- **Assignment context:** [`memory-bank/company-file-analyzer.md`](../memory-bank/company-file-analyzer.md) (schema, invalidation rules, expected metrics)
- **Sample CSV:** [`incidents-brasaland.csv`](./incidents-brasaland.csv) — **100 data rows** (PII-bearing; analyze only inside this monorepo; do not send to external AI tools)

```bash
python3 scripts/analyze.py scripts/incidents-brasaland.csv
```

Missing files, unreadable CSV, and export write failures print to stderr and exit with code `1`.

Optional console prompt exports `results.csv` in the current working directory (`metric`, `value`, `percentage`).

The script imports shared analysis from `services/api/app/incidents/analysis.py` (same logic as `POST /api/incidents/analyze`).

> _Spanish version: [README.es.md](./README.es.md)._
