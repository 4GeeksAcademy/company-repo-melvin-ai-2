# Company File Analyzer — Project Context

## Repository rule
Build this challenge on a **fork of the existing company monorepo**. Do not create a separate new repository.

## Canonical analysis context
Full schema, invalidation rules, and expected metrics for Brasaland live in:

[`.agents/rules/incident-report-processor/context.md`](.agents/rules/incident-report-processor/context.md)

## Sample input
- **File:** [`data/incidents-brasaland.csv`](data/incidents-brasaland.csv)
- **Privacy:** Contains customer identifiers and contact-related fields. Do **not** send this file to external AI tools. Analyze only inside this monorepo.

## Phase 1 entry point
```bash
python3 scripts/analyze.py data/incidents-brasaland.csv
```

See [`scripts/README.md`](scripts/README.md).

## Phase 2 (next)
Backend API + web UI for upload, on-screen summary, and CSV download — reusing the same validation/metric logic.
