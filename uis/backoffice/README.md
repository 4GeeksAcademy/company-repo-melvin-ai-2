# Brasaland Backoffice (`uis/backoffice`)

Internal Next.js workspace for Brasaland operations, the Supplier Directory, and kitchen inventory.

```text
uis/backoffice/
  app/
    suppliers/
    backoffice/inventory/
      products/
      orders/
        inbound/
        outbound/
  lib/
    inventory.ts
```

- **Overview** (`/`) — operations metrics from monorepo root `src/`
- **Suppliers** (`/suppliers`) — Lucía’s supplier directory (FastAPI + TinyDB)
- **Inventory** (`/backoffice/inventory/...`) — ingredients, deliveries, consumption/waste, order history (FastAPI + Supabase)

CONTEXT: [`memory-bank/supplier-directory.md`](../../memory-bank/supplier-directory.md), [`memory-bank/inventory-ui.md`](../../memory-bank/inventory-ui.md)

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
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3101/suppliers` or `http://localhost:3101/backoffice/inventory/products`.

`.env.local` (gitignored) should include the lesson inventory origin, same FastAPI process as suppliers:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_INVENTORY_API_URL=http://localhost:8000
```

## Verify

```bash
npm run lint
npm run build
```
