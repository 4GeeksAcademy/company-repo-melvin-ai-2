# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

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
