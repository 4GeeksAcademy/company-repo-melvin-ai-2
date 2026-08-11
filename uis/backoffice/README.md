# Brasaland Backoffice (`uis/backoffice`)

Internal Next.js workspace for Brasaland operations and the Supplier Directory.

```text
uis/backoffice/
  app/
    suppliers/
```

- **Overview** (`/`) — operations metrics from monorepo root `src/`
- **Suppliers** (`/suppliers`) — Lucía’s supplier directory (FastAPI + TinyDB)

CONTEXT: [`memory-bank/supplier-directory.md`](../../memory-bank/supplier-directory.md)

## Run

API first (port 8000):

```bash
cd services/api
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Then:

```bash
cd uis/backoffice
npm install
npm run dev
```

Open `http://localhost:3101/suppliers`.

Optional: `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`).

## Verify

```bash
npm run lint
npm run build
```
