# Brasaland API (`services/api`)

FastAPI service for Brasaland internal tools:

1. **Incident Report Processor** — CSV analysis shared with `scripts/analyze.py`
2. **Supplier Directory** — TinyDB-backed CRUD for Lucía’s procurement directory

Canonical CONTEXT:

- Incidents: [`memory-bank/company-file-analyzer.md`](../../memory-bank/company-file-analyzer.md)
- Suppliers: [`memory-bank/supplier-directory.md`](../../memory-bank/supplier-directory.md)

## Setup

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Or with uv:

```bash
cd services/api
uv sync
```

## Seed suppliers

Idempotent seeder loads the 15 CONTEXT suppliers into TinyDB (`data/suppliers.json`). Prefer:

```bash
# after pip install -e . / uv sync
uv run seed
# or
python seed.py
```

On API startup, if the suppliers table is empty, the same seeder runs automatically.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

## Incident endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/incidents/analyze` | Upload a CSV (`multipart/form-data` field `file`); returns JSON summary |
| `GET` | `/api/incidents/results/export` | Download the most recent analysis as `results.csv` |

## Supplier endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/suppliers` | Create supplier (422 on invalid category / currency–country mismatch) |
| `GET` | `/suppliers` | List suppliers; optional `?country=` and `?category=` |
| `GET` | `/suppliers/{id}` | Get one supplier |
| `PATCH` | `/suppliers/{id}/rate` | Update `rate_per_unit` and set `updated_at` |
| `PATCH` | `/suppliers/{id}/status` | Set `active` or `suspended` |
| `DELETE` | `/suppliers/{id}` | Remove erroneous row (ops normally suspend) |

Backoffice UI: `uis/backoffice` on port **3101** (`/suppliers`).
