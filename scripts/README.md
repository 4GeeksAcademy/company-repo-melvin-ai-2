# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

## Incident Report Processor (Phase 1)

- **Script:** [`analyze.py`](./analyze.py)
- **Assignment context:** [`memory-bank/company-file-analyzer.md`](../memory-bank/company-file-analyzer.md) (schema, invalidation rules, expected metrics)
- **Sample CSV:** [`data/incidents-brasaland.csv`](../data/incidents-brasaland.csv) — **100 data rows** (PII-bearing; analyze only inside this monorepo; do not send to external AI tools)

```bash
python3 scripts/analyze.py data/incidents-brasaland.csv
```

Expected against the 100-row sample: 100 total · 96 valid · 4 invalid · satisfaction average **3.46**.

Optional console prompt exports `results.csv` in the current working directory (`metric`, `value`, `percentage`).

The script imports shared analysis from `services/api/app/incidents/analysis.py` (same logic as `POST /api/incidents/analyze`).

> _Spanish version: [README.es.md](./README.es.md)._
