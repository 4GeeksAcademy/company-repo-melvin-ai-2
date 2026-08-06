# Brasaland Incident API (`services/api`)

FastAPI service that runs the same Brasaland incident validation and metrics as Phase 1 (`scripts/analyze.py`), using shared logic in `app/incidents/analysis.py`.

Grading acceptance for this assignment uses the **100-row** sample at `data/incidents-brasaland.csv` (see [`memory-bank/company-file-analyzer.md`](../../memory-bank/company-file-analyzer.md)).

## Setup

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

From `services/api`:

```bash
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/incidents/analyze` | Upload a CSV (`multipart/form-data` field `file`); returns JSON summary |
| `GET` | `/api/incidents/results/export` | Download the most recent analysis as `results.csv` |

Errors (empty file, wrong extension, bad encoding, missing columns) return `400` with a descriptive `detail` message. Export without a prior analysis returns `404`.

## Context

Field names, categories (`CUSTOMER_COMPLAINT`, `EQUIPMENT`, `SUPPLY`, `FOOD_QUALITY`, `STAFF`), statuses (`OPEN`, `CLOSED`, `DISCARDED`), invalidation rules, and expected metrics for the **100-row** sample are documented in [`memory-bank/company-file-analyzer.md`](../../memory-bank/company-file-analyzer.md).
