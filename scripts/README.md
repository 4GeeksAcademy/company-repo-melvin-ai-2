# `scripts` folder

This folder contains **helper scripts** for the monorepo: development automation, maintenance utilities, repetitive tasks (setup, lint, migrations, data generation, etc.), and internal tooling.

- **Main purpose**: group support tools that do not belong to a specific app, agent, or pipeline but make the team’s work easier.
- **Recommendation**: document each script (what it does, parameters, requirements, usage examples) and keep them reproducible (and safe) across environments.

## Incident Report Processor (Phase 1)

- **Script:** [`analyze.py`](./analyze.py)
- **Context:** [`.agents/rules/incident-report-processor/context.md`](../.agents/rules/incident-report-processor/context.md)
- **Sample CSV:** [`data/incidents-brasaland.csv`](../data/incidents-brasaland.csv) (PII-bearing — analyze only inside this monorepo; do not send to external AI tools)

```bash
python3 scripts/analyze.py data/incidents-brasaland.csv
```

Optional console prompt exports `results.csv` in the current working directory (`metric`, `value`, `percentage`).

> _Spanish version: [README.es.md](./README.es.md)._
