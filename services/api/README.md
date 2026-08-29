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
- Identity (Sprint 1): [`docs/masterplan.md`](../../docs/masterplan.md) · [`docs/master_instructions.md`](../../docs/master_instructions.md)

## Setup

```bash
cd services/api
uv sync
```

Copy [`.env.example`](./.env.example) to `.env` and set `SECRET_KEY`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `RESEND_API_KEY`, `RESET_TOKEN_EXPIRE_MINUTES`, and `PUBLIC_APP_URL`. Never commit `.env`.

Python 3.12 is pinned in `.python-version` so `python-jose[cryptography]` can install a cryptography wheel (newer cryptography builds from source and needs OpenSSL headers).

## Seed

```bash
uv run seed
uv run seed-auth
```

On API startup, empty supplier TinyDB is seeded, and an empty auth TinyDB seeds Lucía Fernández (`admin`) from the env vars above. Data files: `data/suppliers.json`, `data/auth.json` (gitignored).

## Run

```bash
uv run uvicorn main:app --reload --port 8000
```

Health: `GET http://localhost:8000/health` (public) · Docs: `http://localhost:8000/docs`

Unhandled errors return JSON `{ "detail": "..." }` with `400`, `404`, `422`, or `500`. Response bodies never include stack traces, file paths, or secrets. Validation `422` includes field `loc` / `msg` only (no submitted `input` values).

## Auth endpoints

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/users` | Public register |
| `GET` | `/users` | Bearer |
| `GET` | `/users/{id}` | Bearer; self or admin |
| `PUT` | `/users/{id}` | Bearer; self or admin (role: admin only) |
| `DELETE` | `/users/{id}` | Bearer; self or admin |
| `GET` | `/profiles/me` | Bearer |
| `PUT` | `/profiles/me` | Bearer; owner |
| `POST` | `/auth/login` | Public; `{ "email", "password" }` |
| `GET` | `/auth/me` | Bearer |
| `POST` | `/auth/forgot-password` | Public; always `200`; emails a reset link via Resend when the address exists |
| `POST` | `/auth/reset-password` | Public; `{ "token", "new_password" }`; one-time; `400` if invalid/expired/used |
| `POST` | `/auth/change-password` | Bearer; `{ "current_password", "new_password" }`; `400` if current is wrong |

`GET /suppliers*`, supplier mutations, `POST /api/incidents/analyze`, and `GET /api/incidents/results/export` require a Bearer token. `GET /health` stays public.

Reset links use `PUBLIC_APP_URL` (default `http://localhost:3101`) as `{PUBLIC_APP_URL}/reset-password?token=...`. The same path exists on incident web (`:3102`) and talent tracker (`:3000`) if you change the origin.

## Supplier endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/suppliers` | Create supplier |
| `GET` | `/suppliers` | List; optional `?country=` / `?category=` |
| `GET` | `/suppliers/{id}` | Get one |
| `PATCH` | `/suppliers/{id}/rate` | Update rate + `updated_at` |
| `PATCH` | `/suppliers/{id}/status` | Update status |
| `DELETE` | `/suppliers/{id}` | Delete |

Frontend: `uis/backoffice` on port **3101** (`/suppliers`). After this sprint those calls return `401` until the UI sends the JWT (Sprint 2).

