# Brasaland API serialization audit

Canonical app: `services/api/main.py` (not `app/main.py`). Consumers: `@repo/auth`, `uis/backoffice`, `uis/web` incident analysis.

**Locked decisions**

- CSV export stays `text/csv` (incident UI downloads `results.csv`).
- `GET /health` and `POST /suppliers/admin/seed` get named JSON `response_model`s.
- `DELETE` routes stay **204 No Content** (`response_model=None`).
- Unauthenticated auth must not echo email. `GET /auth/me` may return email (profile UI).
- Inventory **order list** is a flat projection (`ingredient_name`, `unit`). Nested `IngredientPublic` stays on inbound/outbound **write** responses so the confirmation still has the ingredient the kitchen just logged.
- Supplier list keeps `SupplierResponse` (directory table reads contact email, rate, status, notes).

Status: 🟢 explicit `response_model` that matches the consumer · ⚠️ schema exists but over-fetches or echoes more than the client needs · ❌ no `response_model` / raw dict / ORM dump.

## Auth (reviewed first)

| Method | Path | Purpose | Original | After | Status |
| --- | --- | --- | --- | --- | --- |
| POST | `/auth/login` | Issue JWT | `TokenResponse` `{ access_token, token_type }` — no email, no user row | unchanged | 🟢 |
| GET | `/auth/me` | Signed-in identity for internal UIs | `AuthMeResponse` `{ email, role, profile }` — profile UI needs this | unchanged (email allowed here) | 🟢 |
| POST | `/auth/forgot-password` | Start reset; always 200 | `MessageResponse` `{ ok: true }` — does not echo email | unchanged | 🟢 |
| POST | `/auth/reset-password` | Consume reset token | `MessageResponse` — token stays in the request | unchanged | 🟢 |
| POST | `/auth/change-password` | Change password while signed in | `MessageResponse` — hashes stay in TinyDB | unchanged | 🟢 |

Input vs output: `LoginRequest` / `ForgotPasswordRequest` / `ResetPasswordRequest` / `ChangePasswordRequest` are request-only. None of these schemas include `hashed_password` or reset-token rows.

## Users and profiles

| Method | Path | Purpose | Original | After | Status |
| --- | --- | --- | --- | --- | --- |
| POST | `/users` | Public register | `UserPublic` including **email** (unauthenticated echo) | `RegisterResponse`: `id`, `is_active`, `role`, `created_at` — **no email**. Client then `POST /auth/login` with the form values. | ⚠️ → 🟢 |
| GET | `/users` | Authenticated directory | `list[UserPublic]` (id, email, is_active, role, created_at) | `list[UserListItem]`: `id`, `email`, `role` (directory tests and admin listing need email; drop `is_active` / `created_at`) | ⚠️ → 🟢 |
| GET | `/users/{id}` | One operator (self or admin) | `UserPublic` | unchanged | 🟢 |
| PUT | `/users/{id}` | Update email/role | Request `UserUpdate`; response `UserPublic` | unchanged (input ≠ output) | 🟢 |
| DELETE | `/users/{id}` | Remove operator | 204, no `response_model` | 204, `response_model=None` | 🟢 |
| GET | `/profiles/me` | Profile contact | `ProfilePublic` | unchanged | 🟢 |
| PUT | `/profiles/me` | Update contact | Request `ProfileUpdate`; response `ProfilePublic` | unchanged | 🟢 |

`public_user()` already strips `hashed_password` before any response model.

## Health and suppliers

| Method | Path | Purpose | Original | After | Status |
| --- | --- | --- | --- | --- | --- |
| GET | `/health` | Liveness | `dict` `{ status: ok }`, no `response_model` | `HealthResponse` `{ status: "ok" }` | ❌ → 🟢 |
| POST | `/suppliers` | Create supplier | Request `SupplierCreate`; response `SupplierResponse` | unchanged | 🟢 |
| GET | `/suppliers` | Directory table | `list[SupplierResponse]` — same fields the backoffice table shows (name, country, categories, rate, currency, status, contact_email, notes) | unchanged; list = detail because the consumer is the same table | 🟢 |
| GET | `/suppliers/{id}` | One supplier | `SupplierResponse` | unchanged | 🟢 |
| PATCH | `/suppliers/{id}/rate` | Update rate | Request `RateUpdate`; response `SupplierResponse` | unchanged | 🟢 |
| PATCH | `/suppliers/{id}/status` | Update status | Request `StatusUpdate`; response `SupplierResponse` | unchanged | 🟢 |
| DELETE | `/suppliers/{id}` | Remove supplier | 204, no `response_model` | 204, `response_model=None` | 🟢 |
| POST | `/suppliers/admin/seed` | Demo seed helper | `{ inserted: int }` dict, no `response_model` | `SeedResponse` `{ inserted: int }` | ❌ → 🟢 |

## Inventory

| Method | Path | Purpose | Original | After | Status |
| --- | --- | --- | --- | --- | --- |
| GET | `/inventory/products` | Ingredient stock list | `list[IngredientRead]` (CONTEXT fields + `current_stock`) | unchanged — list UI needs stock, sku, unit, country | 🟢 |
| POST | `/inventory/products` | Create SKU | Request `IngredientCreate`; response `IngredientRead` | unchanged | 🟢 |
| GET | `/inventory/products/{id}` | One SKU | `IngredientRead` | unchanged | 🟢 |
| POST | `/inventory/orders/inbound` | Log delivery | Request `InboundCreate`; response `InboundRead` with nested `IngredientPublic` | keep nest on **write** confirmation; documented | 🟢 |
| POST | `/inventory/orders/outbound` | Log consumption/waste | Request `OutboundCreate`; response `OutboundRead` with nested `IngredientPublic` | same as inbound | 🟢 |
| GET | `/inventory/orders` | History table | `list[OrderListItem]` nested full `IngredientPublic` (sku, category, country unused by the table) | flat `ingredient_name`, `unit` plus existing order fields | ⚠️ → 🟢 |

ORM rows are never returned; inventory already mapped through Pydantic.

## Incidents

| Method | Path | Purpose | Original | After | Status |
| --- | --- | --- | --- | --- | --- |
| POST | `/api/incidents/analyze` | Upload CSV; summary for `uis/web` | Untyped `dict` from `result_to_summary` — **no `response_model`** | `IncidentAnalysisResponse` matching the summary the incident UI already reads | ❌ → 🟢 |
| GET | `/api/incidents/results/export` | Download metrics CSV | `Response` `text/csv`; attachment `results.csv` | unchanged file contract (not JSON; not an ORM dump) | 🟢 |

## Target field lists (after)

- `HealthResponse`: `status`
- `RegisterResponse`: `id`, `is_active`, `role`, `created_at`
- `UserListItem`: `id`, `email`, `role`
- `UserPublic`: `id`, `email`, `is_active`, `role`, `created_at`
- `OrderListItem`: `type`, `id`, `ingredient_id`, `ingredient_name`, `unit`, `quantity`, `location_id`, `created_at`, `user_uuid`, `supplier_name?`, `reason?`
- `SeedResponse`: `inserted`
- `IncidentAnalysisResponse`: `source_file`, `totals`, `invalid_breakdown`, `by_category`, `by_status`, `satisfaction` (same keys as `uis/web` `AnalysisSummary`)

## Implementation notes

- Duplicate trailing-slash aliases (`/users/`, `/suppliers/`) share the same serializers; not listed twice.
- `app/main.py` is a leftover incident-only app (not what uvicorn runs). Its `GET /health` still uses `HealthResponse` so every FastAPI entrypoint in `services/api` has an explicit serializer.

## Verification

- `uv run pytest` (git root) — **51 passed**
- `cd uis/backoffice && npx tsc --noEmit` — passed after flattening `OrderRow`
- Live API on `http://localhost:8000` (same contracts as `/docs`), 18 September 2026:
  - `GET /health` → 200 `{ "status": "ok" }` (`HealthResponse`)
  - `POST /users` → 201 keys `id`, `is_active`, `role`, `created_at` — **no `email`**, no password fields (`RegisterResponse`)
  - `POST /auth/login` → 200 `{ "access_token", "token_type" }` — **no `email`** (`TokenResponse`)
  - `GET /auth/me` (Bearer) → 200 `{ "email", "role", "profile" }` — email is the signed-in operator (`AuthMeResponse`)
  - `GET /inventory/orders` (Bearer) → 200 list of 9 rows with `ingredient_name` + `unit`, **no nested `ingredient`**

