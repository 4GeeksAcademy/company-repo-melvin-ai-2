# Brasaland Identity — Master Instructions

Ordered instructions for completing the combined authentication project. Architecture and locked decisions live in [`masterplan.md`](./masterplan.md). This file is the **do-this-in-order** checklist.

Work on branch `feature/brasaland-auth`. Do not create a new repository. Finish each part before starting the next.

**Sources**

- [AUTH-01 — User Authentication API](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-api/README.md)
- [AUTH-02 — Authentication Flows in the Frontend](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-flows/README.md)
- [AUTH-03 — Password Reset Flow](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-restore/README.md)

**Brasaland adjustments (locked)**

- One branch (`feature/brasaland-auth`), not `feature/auth-api` then `feature/auth-frontend` then `feature/password-reset`, unless the instructor later wants three PRs.
- Shared UI/client in `packages/auth` (`@repo/auth`). Internal apps import it; do not copy login/register/account three times.
- Talent Pipeline Tracker candidates stay on the 4Geeks Playground API. Brasaland JWT is for login, guards, and profile only.
- Sprint 3 email: **Resend**.
- Seed Lucía Fernández as `admin` so suppliers and incident tools can be demoed without registering.
- Public website (`uis/website`, including `/brasa-points`) stays fully public. Brasa Points is not this User/Profile system.

---

## Part 1 — AUTH-01: Lock the Brasaland API

**Goal:** No route that modifies or exposes sensitive Brasaland data is reachable without a valid session.

**Where:** `services/api` only (`main.py` is the canonical app). Users and profiles in TinyDB `data/auth.json` — not `data/suppliers.json`.

**Note:** After this part, backoffice suppliers and incident upload will return `401`. That is expected until Part 2.

### How to start

1. Stay on `feature/brasaland-auth`.
2. From `services/api`, install with `uv` (never `pip install` or `pipenv`):

```bash
uv add "python-jose[cryptography]" "libpass[bcrypt]"
```

3. Put `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `SEED_ADMIN_EMAIL`, and `SEED_ADMIN_PASSWORD` in a gitignored `.env`. Document the **names** in `services/api/.env.example`.

### What you need to do

#### User model and CRUD

- [ ] Create a `User` model in **TinyDB** (`data/auth.json`) with at least: `id`, `email`, `hashed_password`, `is_active`, `role`, `created_at`. Do **not** store display name or contact fields on `User`.
- [ ] `role` accepts only `admin`, `manager`, or `user`. Use an Enum or field validator. `POST /users` defaults to `user`.
- [ ] Service layer: create user, get user by ID, get user by email, update user, delete user.
- [ ] REST under `/users`:
  - `POST /users` — register (hash password first). Optional `name`, `phone`, `address` create the linked `Profile` in the same operation.
  - `GET /users` — list all users (protected).
  - `GET /users/{id}` — get one user (protected).
  - `PUT /users/{id}` — update credential fields such as `email`, and `role` when the caller is an `admin` (protected; only the user themselves or an admin).
  - `DELETE /users/{id}` — delete user (protected). Also remove the linked profile.
- [ ] Seed Lucía Fernández: `role=admin`, hashed password from env, linked Profile. Idempotent (startup if auth DB empty, plus a `uv run` helper).

#### Profile model and endpoints

- [ ] `Profile` in TinyDB, one-to-one with `User` via `user_id`, with at least: `id`, `user_id`, `name`, `phone`, `address`.
- [ ] Routes under `/profiles`:
  - `GET /profiles/me` (protected) — authenticated user’s profile.
  - `PUT /profiles/me` (protected) — update `name`, `phone`, `address`. Owner only.

#### Authentication endpoints

- [ ] `POST /auth/login` — `{ email, password }`, validate, return a signed JWT.
- [ ] `GET /auth/me` (protected) — `email`, `role`, plus linked Profile (name and contact).

#### Token and dependency

- [ ] `get_current_user`: extract `Authorization: Bearer <token>`, decode and validate JWT (`python-jose`), load user from TinyDB, raise `HTTPException(401)` on any failure. Use FastAPI `OAuth2PasswordBearer`. JWT claims include the TinyDB user `id`.
- [ ] Token expiry from `ACCESS_TOKEN_EXPIRE_MINUTES`. Signing secret from `.env` (`SECRET_KEY`). Never hardcode.

#### Route protection

Apply `get_current_user` to every route that should not be public. At minimum: all `/users` except `POST /users`, `/auth/me`, **and at least 5 existing Brasaland routes** outside `/users` and `/auth`. Lock all of these (`GET /health` stays public):

- [ ] `GET /suppliers` and `POST /suppliers`
- [ ] `GET /suppliers/{id}`
- [ ] `PATCH /suppliers/{id}/rate`
- [ ] `PATCH /suppliers/{id}/status`
- [ ] `DELETE /suppliers/{id}`
- [ ] `POST /suppliers/admin/seed`
- [ ] `POST /api/incidents/analyze`
- [ ] `GET /api/incidents/results/export`
- [ ] `401 Unauthorized` when there is no valid token. `403 Forbidden` when a user accesses a resource they do not own.

#### Testing (FastAPI `/docs`)

- [ ] Register via `POST /users` → login → copy token → use token on a protected route.
- [ ] Login as Lucía → `GET /suppliers` succeeds.
- [ ] Protected route without a token → `401`.
- [ ] Expired or malformed token → `401`.
- [ ] User A updates user B’s credentials or profile → `403`.

#### Important (do not skip)

- User and Profile stay in **TinyDB only** — now and after Supabase. No user/profile tables in PostgreSQL. Other modules may store TinyDB `id` as `user_uuid`.
- Stateless JWT only. No session or cookie auth.
- Never store plaintext passwords. `from passlib.hash import bcrypt` (libpass fork). Install `libpass[bcrypt]`, not unmaintained `passlib`.

#### What we will evaluate (Part 1)

- [ ] User CRUD is reachable via the API.
- [ ] Each User has a linked Profile; name/phone/address on Profile, not User.
- [ ] Role enum + default `user` on `POST /users`.
- [ ] Passwords hashed at create and compared at login.
- [ ] Login returns a valid signed JWT.
- [ ] `get_current_user` decodes the token and identifies the user.
- [ ] Protected routes return `401` without a valid token.
- [ ] Cross-user access/update returns `403`.
- [ ] Expiry and signing secret from environment variables.
- [ ] Routes under `/auth`, `/users`, `/profiles`.
- [ ] At least 5 existing routes outside `/users` and `/auth` require a token.
- [ ] User/Profile remain TinyDB-only.
- [ ] Protected routes still work with a valid token (no regressions).

Role-based permissions on every route are **not** required.

**Stop here until Part 1 passes.** Then go to Part 2.

---

## Part 2 — AUTH-02: Connect internal UIs

**Goal:** Close the loop. Internal Brasaland apps send the JWT and hide views from anonymous users. The public website stays public.

**Where:** `packages/auth` (`@repo/auth`) plus thin App Router pages in `uis/backoffice`, `uis/web`, and `uis/talent-pipeline-tracker`. Do not build a separate auth app. Do not put APIs in Next.js route handlers.

### How to start

1. API from Part 1 must be running (`uvicorn` on port 8000).
2. Stay on `feature/brasaland-auth`.
3. Create `packages/auth`. Each internal UI: `"@repo/auth": "file:../../packages/auth"` and Next `transpilePackages: ["@repo/auth"]`. Do not change root npm workspaces.

### Complementary rules (frontend JWT)

1. **Store** the token in `localStorage` after login/register.
2. **Read** it on every **Brasaland** protected API call: `Authorization: Bearer <token>` (`authFetch` in `@repo/auth`).
3. **Protect routes** with a **client** layout guard or hook. Next.js middleware cannot read `localStorage`; do not use middleware unless the token is also in a cookie.
4. **Clear** the token on logout and on `401`, then redirect to `/login`.

Do **not** attach the Brasaland JWT to Talent Pipeline Tracker candidate calls (`uis/talent-pipeline-tracker/lib/api.ts` + `NEXT_PUBLIC_API_URL` = Playground).

### What you need to do

#### Authentication views (implement once in `@repo/auth`; thin `page.tsx` in each internal app)

- [ ] `/login` — email and password. Success: store token, redirect to that app’s main authenticated view. Failure: clear error.
- [ ] `/register` — `POST /users` (optional profile fields), then `POST /auth/login`, store token, redirect. Failure: field-level validation errors.

#### Account management views

- [ ] `/account/profile` — email plus `name`, `phone`, `address` from `GET /auth/me`. Edit name/contact via `PUT /profiles/me` with the Bearer token.

#### Route protection

- [ ] Identify every internal view that needs a session:
  - `uis/backoffice`: `/` and `/suppliers`
  - `uis/web`: `/` and `/incidents`
  - `uis/talent-pipeline-tracker`: candidate views
- [ ] Client guard: no/invalid token in `localStorage` → `/login`.
- [ ] `uis/website` entirely unaffected — no token check, no redirect (`/` and `/brasa-points` stay public).

#### Token lifecycle

- [ ] Login and registration store the token in `localStorage`.
- [ ] Every protected **Brasaland** API call sends `Authorization: Bearer <token>`:
  - [ ] `uis/backoffice/lib/suppliersApi.ts`
  - [ ] `uis/web/src/lib/api.ts` (analyze **and** export — export cannot stay a bare URL)
- [ ] Logout removes the token and redirects to `/login`.
- [ ] Protected Brasaland `401` clears the token and redirects to `/login`.
- [ ] Talent tracker: add `NEXT_PUBLIC_API_BASE_URL` for Brasaland auth only; keep `NEXT_PUBLIC_API_URL` for Playground candidates with **no** Brasaland JWT.

#### What we will evaluate (Part 2)

- [ ] Login and registration store the token after a successful call.
- [ ] Protected views redirect to `/login` when there is no valid token.
- [ ] Public website works with no authentication check.
- [ ] Profile shows User email and Profile contact; updates via `PUT /profiles/me`.
- [ ] Logout removes the token and redirects.
- [ ] `401` from a protected Brasaland call clears the session and redirects.
- [ ] Forms live in `@repo/auth` (not three copies).
- [ ] Lucía can open `/suppliers` and incident analysis after login.
- [ ] Talent candidate fetches still hit Playground only.

**Stop here until Part 2 passes.** Then go to Part 3.

---

## Part 3 — AUTH-03: Password recovery and change

**Goal:** Reset when forgotten; change while logged in. Real email via **Resend**.

**Where:** API under `/auth` plus forgot/reset/change-password UI in `@repo/auth` (thin routes in the three internal apps). Not on `uis/website`.

### How to start

1. Sign up at [Resend](https://resend.com/), get an API key, store it as `RESEND_API_KEY` in gitignored `.env`. Never commit it.
2. Also set `RESET_TOKEN_EXPIRE_MINUTES` (15–60) and `PUBLIC_APP_URL` (origin for `/reset-password?token=...`).
3. Document variable names in `services/api/.env.example` or `services/api/README.md`.
4. Stay on `feature/brasaland-auth`. API and internal UIs from Parts 1–2 must already work.

### Complementary rules (reset flow)

1. **Request** — user submits email. Server creates a short-lived token, emails `{PUBLIC_APP_URL}/reset-password?token=...`.
2. **Reset** — user submits token + new password. Server checks signature, expiry, **and that the token was not already used**, then hashes and updates.
3. **Confirmation** — redirect to `/login`.

Always show a generic confirmation on forgot-password (no “email not found”). JWT `exp` alone cannot invalidate a used token — persist server-side state (hashed token row, used-token record, or `password_changed_at`).

### What you need to do

#### Backend

- [ ] `POST /auth/forgot-password` — `{ email }`. If the user exists: generate a reset token (15–60 min) and send a Resend email with the reset link. **Always return 200**, whether or not the email was found.
- [ ] `POST /auth/reset-password` — `{ token, new_password }`. Validate signature, expiry, unused. Hash, update user, invalidate token. `400` for invalid, expired, **or already-used** tokens.
- [ ] `POST /auth/change-password` — Bearer required. `{ current_password, new_password }`. Verify current password first. `400` if current is wrong.
- [ ] Resend email includes the reset link and is readable on mobile.
- [ ] API key only in an environment variable; name documented in README or `.env.example`.

#### Frontend (`@repo/auth` + thin routes)

- [ ] `/forgot-password` — call `POST /auth/forgot-password`, always show “If that address is registered, you’ll receive a link shortly”, disable the form after submit.
- [ ] `/reset-password` — confirmation field; read `token` from the query string; `POST /auth/reset-password`. Success → `/login` with a success message. Failure → clear error and a link to `/forgot-password`.
- [ ] `/account/change-password` — current, new, confirm; match new and confirm before the API call.
- [ ] “Forgot your password?” on `/login` → `/forgot-password`.

#### Security

- [ ] Reset tokens expire and cannot be used twice.
- [ ] Forgot-password never reveals whether an email is registered.
- [ ] No API keys in the codebase.

#### Optional (not evaluated)

- HTML email template
- Rate limiting forgot-password per email per hour
- Audit log of password resets

#### What we will evaluate (Part 3)

- [ ] Registered address receives a real Resend email with the reset link.
- [ ] Forgot-password returns `200` for unknown addresses.
- [ ] Token expires and cannot be used after expiry.
- [ ] Reset updates the password and invalidates the token.
- [ ] Reset returns `400` for expired or already-used tokens.
- [ ] `/forgot-password` always shows the generic confirmation.
- [ ] `/reset-password` reads the token, submits, redirects to `/login` on success.
- [ ] Invalid/expired token shows an error and a link back to `/forgot-password`.
- [ ] Login has a visible “Forgot your password?” link.
- [ ] `/account/change-password` validates matching passwords, calls the API, shows success or error.
- [ ] Change-password rejects wrong current password with `400`.
- [ ] No hardcoded secrets.

---

## How to submit

Push `feature/brasaland-auth` and open a pull request against `main` when the instructor is ready (one PR for all three parts unless they ask for three).

PR description should include:

- Which existing API routes are protected and how you verified Part 1 (`/docs`).
- Which views are protected and confirmation that `uis/website` was not affected.
- Email service: **Resend**; env var `RESEND_API_KEY`; confirmation that the full forgot → email → reset → login flow was tested.

Secrets stay out of git. Do not commit `.env`.
