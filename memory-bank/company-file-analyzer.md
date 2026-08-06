# Company File Analyzer — Assignment Context

Brasaland after-sales / operations **Incident Report Processor**. Work stays in this company monorepo fork. Incident CSVs contain PII and must **not** be sent to external AI tools — analyze only inside the platform.

Companion detail for agents also lives at [`.agents/rules/incident-report-processor/context.md`](../.agents/rules/incident-report-processor/context.md). **This memory-bank file is the assignment write-up source of truth** for schema, invalidation rules, and expected metrics on the sample file.

## Sample input (what we validate against)

- **File:** [`data/incidents-brasaland.csv`](../data/incidents-brasaland.csv)
- **Rows:** **100** data rows (plus header) — this is the official test sample for grading
- Production volume may grow much larger later; Phase 1/2 acceptance uses this **100-row** file only

## CSV schema

| Field | Required | Allowed values / notes |
|-------|----------|------------------------|
| `incident_id` | Yes | `BRS-XXXXXX` |
| `date` | Yes | `YYYY-MM-DD` |
| `location_id` | Yes | `COL-01`…`COL-10`, `FLA-01`…`FLA-04` |
| `category` | Yes | See categories below |
| `description` | Yes | Free text, min 5 characters |
| `status` | Yes | `OPEN`, `CLOSED`, `DISCARDED` |
| `customer_id` | No | Optional `CLI-XXXXXX` |
| `satisfaction_score` | Conditional | Integer 1–5; **required when** `status = CLOSED` |
| `reporter_id` | Yes | `MGR-XX` |

### Categories

- `CUSTOMER_COMPLAINT`
- `EQUIPMENT`
- `SUPPLY`
- `FOOD_QUALITY`
- `STAFF`

## Invalid record rules

A row is **invalid** if any rule below applies. Invalid rows are **detected, counted, and excluded** from category/status/satisfaction analysis — never silently dropped.

| Rule | Description |
|------|-------------|
| Missing / invalid `location_id` | Empty or not one of the 14 valid location codes |
| Missing / invalid `category` | Empty or not one of the 5 valid categories |
| Empty / too-short `description` | Empty or fewer than 5 characters |
| Missing `reporter_id` | Empty |
| `CLOSED` with no `satisfaction_score` | Closed case without a recorded score |
| `satisfaction_score` out of range | Present but not an integer from 1 to 5 inclusive |

## Expected results (100-row sample)

| Metric | Expected |
|--------|----------|
| Total rows | **100** |
| Valid | **96** |
| Invalid | **4** |

**Invalid breakdown:** missing `location_id` 1 · invalid/missing category 1 · empty/too-short description 1 · `CLOSED` with no score 1

**Category (valid):** `CUSTOMER_COMPLAINT` 29 · `EQUIPMENT` 17 · `SUPPLY` 22 · `FOOD_QUALITY` 19 · `STAFF` 9

**Status (valid):** `OPEN` 32 · `CLOSED` 50 · `DISCARDED` 14

**Satisfaction (closed with scores):** 50 of 50 scored · average **3.46** (1→4, 2→6, 3→12, 4→19, 5→9)

## How to run

### Phase 1 — script

```bash
python3 scripts/analyze.py data/incidents-brasaland.csv
```

See [`scripts/README.md`](../scripts/README.md).

### Phase 2 — API + UI

- API: [`services/api`](../services/api/README.md) — `POST /api/incidents/analyze`, `GET /api/incidents/results/export`
- UI: [`uis/web`](../uis/web/README.md) — Incident analysis page
- Shared logic: `services/api/app/incidents/analysis.py` (used by CLI and API)
