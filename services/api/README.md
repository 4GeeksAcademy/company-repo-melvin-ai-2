# Brasaland API (`services/api`)

Submission layout (Supplier Directory):

```text
services/api/
  main.py
  models.py
  database.py
  routes/
    suppliers.py
  seed.py
```

Also keeps the Incident Report Processor under `app/incidents/` + `app/routers/incidents.py`.

Canonical CONTEXT:

- Suppliers: [`memory-bank/supplier-directory.md`](../../memory-bank/supplier-directory.md)
- Incidents: [`memory-bank/company-file-analyzer.md`](../../memory-bank/company-file-analyzer.md)

## Setup

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Or with uv: `uv sync`

## Seed suppliers

```bash
uv run seed
# or
python seed.py
```

On API startup, if TinyDB is empty, the same seeder runs automatically. Data file: `data/suppliers.json`.

## Run

```bash
uvicorn main:app --reload --port 8000
```

Health: `GET http://localhost:8000/health` · Docs: `http://localhost:8000/docs`

## Supplier endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/suppliers` | Create supplier |
| `GET` | `/suppliers` | List; optional `?country=` / `?category=` |
| `GET` | `/suppliers/{id}` | Get one |
| `PATCH` | `/suppliers/{id}/rate` | Update rate + `updated_at` |
| `PATCH` | `/suppliers/{id}/status` | Update status |
| `DELETE` | `/suppliers/{id}` | Delete |

Frontend: `uis/backoffice` on port **3101** (`/suppliers`).
