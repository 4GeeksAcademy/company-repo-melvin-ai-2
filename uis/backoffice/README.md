# Brasaland Backoffice

Internal Next.js workspace for Brasaland operations.

- **Overview** (`/`) — sales, margin, waste, and location performance using Milestone 2 TypeScript logic from the monorepo root `src/`.
- **Suppliers** (`/suppliers`) — Lucía’s supplier directory against the FastAPI TinyDB API.

Supplier CONTEXT: [`memory-bank/supplier-directory.md`](../../memory-bank/supplier-directory.md).

## Run

Start the API first (port 8000):

```bash
cd services/api
source .venv/bin/activate   # or uv
uvicorn app.main:app --reload --port 8000
```

Then the backoffice (port **3101**):

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

Do not copy operations calculations into this application. Extend the root `src` module and import the result. Supplier CRUD talks to `services/api` only.
