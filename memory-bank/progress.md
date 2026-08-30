# Progress

## Current Milestone
Error handling audit on `feature/error-handling-audit`: AuthGuard now confirms the session, and remaining banners expose Try again plus home/support.

## Completed
- Tightened `AuthGuard` to call `GET /auth/me`: no token or 401 returns to `/login`; network or other failures show `ErrorBanner` with retry (plus home and `hello@brasaland.com`). `finally` clears the checking state.
- Wired `onRetry` on forgot/register/reset/change-password and profile save (`requestSubmit`), and on talent candidate form, notes add/delete, and status/stage patches. Softened leftover “failed to…” fallbacks to human copy.
- Gap-fill after `3313c42`: split supplier load vs mutation errors so the table stays visible; incident export retry re-downloads; talent API sanitizes technical `detail`; notes/list use `?.` / `?? []`; TinyDB writes raise `PersistenceError`; seed CLIs exit `1` on unexpected failure.
- Applied a consistent error-handling strategy across `@repo/auth`, backoffice suppliers, incident web, talent tracker, FastAPI, and `scripts/analyze.py` (retry / home / `hello@brasaland.com`; no status codes or stack traces in client messages).
- Added the business and technical memory bank, root agent workflow, scoped rules, and delivery-verification skill.
- Reorganized agent config to `.agents/rules/` and `.agents/skills/` (including dual-currency and delivery-verification skills).
- Added always-on `.agents/rules/company-context.md` so every milestone uses Brasaland only.
- Rebuilt the complete public website as reusable Next.js components at `uis/website`.
- Added the validated Brasa Points registration route at `/brasa-points`.
- Restored the canonical Milestone 2 models, sample data, and pure utilities under root `src`.
- Built a distinct backoffice operations dashboard that imports and visibly renders those utilities.
- Delivered Company File Analyzer Phase 1 + Phase 2 (CLI, API, `uis/web`).
- Delivered Supplier Directory: CONTEXT in `memory-bank/supplier-directory.md`, TinyDB seeder (15 suppliers), FastAPI `/suppliers` CRUD, `uis/backoffice/app/suppliers` UI (filters, create, rate, status).
- Wrote Brasaland Identity master plan at `docs/masterplan.md` (one branch, three sprint checklists).
- Sprint 1 AUTH-01: TinyDB User/Profile, JWT, `get_current_user`, protected suppliers + incidents, seeded Lucía Fernández as admin.
- Sprint 2 AUTH-02: `@repo/auth` shared package; login/register/profile + client guard in backoffice, incident web, and talent tracker; Bearer on Brasaland API calls; Playground candidate API unchanged; website untouched.
- Sprint 3 AUTH-03: forgot/reset/change-password API + `@repo/auth` forms and thin routes; reset tokens hashed in TinyDB (expiry + one-time); Resend wired behind `RESEND_API_KEY`.

## Verification
- AuthGuard + retry nits (2026-08-30): lint + `tsc --noEmit` + production build passed for `uis/backoffice`, `uis/web`, and `uis/talent-pipeline-tracker`. Browser with API down: stale token on `/suppliers` shows connection copy plus Try again / home / support; retry keeps the banner; forgot-password and register retries re-submit. With API up: Lucía session check loads 15 suppliers. Talent: after login, intercepted note POST and status PATCH show human connection copy plus Try again; retry re-fires the same call. Public `/brasa-points` still has no fetch three-state. Reset missing-token banner still has home/support only (nothing to retry).
- Error handling gap-fill (2026-08-29): `scripts/analyze.py` missing file exits `1`; usage without a path exits `1`; sample CSV still reports 100/96/4 and average **3.46**. API: `GET /health` 200; malformed login JSON 400 human body; incomplete login 400; `/suppliers` without token 401. Lint + `tsc --noEmit` + production build passed for `uis/backoffice`, `uis/web`, and `uis/talent-pipeline-tracker`. Browser: wrong-password login shows human copy plus Try again / Back to home / Contact support (no traceback); Lucía `/suppliers` loads; invalid rate keeps the table visible with a CTA banner; incidents reachable after web login. Public `/brasa-points` on `:3001` returns 200 (client-only form, no fetch three-state). Talent home CTA re-click after a separate-origin login was not re-run; ErrorMessage still includes retry/home/support in code.
- Error handling (2026-08-28): `scripts/analyze.py` missing file exits `1`; sample CSV still reports 100/96/4 and average **3.46**. API: `GET /health` 200; malformed login JSON 400 human body; incomplete login 400; `/suppliers` without token 401; register 422 has `loc`/`msg`/`type` only (no `input`). Lint + production build passed for `uis/backoffice`, `uis/web`, and `uis/talent-pipeline-tracker`.
- `uis/website`: lint passed; Next.js production build passed.
- `uis/backoffice`: lint passed; Next.js production build passed (includes `/login`, `/register`, `/account/profile`, `/suppliers`).
- `uis/web`: lint passed; Next.js production build passed (includes `/login`, `/incidents`).
- `uis/talent-pipeline-tracker`: lint passed; Next.js production build passed (includes `/login` and candidate routes).
- Supplier API smoke tests: seed inserts 15; list/filter; 422 on currency/category errors; rate PATCH sets `updated_at`; seeder idempotent.
- Development smoke tests returned HTTP 200 with expected visible content for website `/`, website `/brasa-points`, and backoffice `/`.
- Backoffice calculations are imported from root `src`; no calculation implementation was copied into the UI.
- Brasaland Identity Sprint 1 API checks (curl against `:8000`): `GET /health` 200 public; `/suppliers` and incident analyze 401 without token; Lucía login 200; `GET /auth/me` returns Lucía + Profile; `/suppliers` 200 with Bearer (15 rows); register `POST /users` 201 role `user`; other user GET/PUT 403; malformed token 401; `/docs` 200. Developer confirmed Swagger Authorize as Lucía.
- Sprint 2: production builds for the three internal apps passed. Public website files were not changed.
- Sprint 3 re-check: API forgot always 200 with identical bodies; reset one-time + expired 400; change-password wrong-current 400 then success; Lucía seed login still works. Resend key loaded: Yahoo forgot-password 200 with no Resend exception; Lucía send still refused by onboarding (only `ewell_melvin@yahoo.com`). UI: forgot link, generic confirmation, reset without token, reset success → `/login`, change-password mismatch; website public. Earlier browser log already showed Yahoo forgot → reset 200 → login 200.
- Global_Criteria live grade (2026-08-27): API FAIL COUNT 0 (CRUD, Profile 1:1, JWT, 401/403, TinyDB bcrypt, suppliers 15, incident analyze+export, forgot/reset/change-password, env secrets). Browser FAIL COUNT 0 (register token, logout, guards, website `/` and `/brasa-points`, profile save, 401 redirect, Lucía suppliers + incidents, Playground with no Bearer, forgot/reset/change-password UI). Score: Part 1 13/13, Part 2 9/9, Part 3 15/15, **total 37/37 Pass**.

## Next Steps
- Optional: verify a Resend domain if Lucía (or any non-Yahoo inbox) must receive reset mail.

## Documentation
- Updated `docs/ARCHITECTURE_PROPOSAL.md` into a CTO-facing FastAPI backend proposal.
- Company File Analyzer CONTEXT: `memory-bank/company-file-analyzer.md`.
- Supplier Directory CONTEXT: `memory-bank/supplier-directory.md` (root `CONTEXT.md` points there; `scripts/CONTEXT-brasaland.en.md` is a pointer).
- Brasaland Identity: [`docs/masterplan.md`](../docs/masterplan.md) and [`docs/master_instructions.md`](../docs/master_instructions.md).
- API env names: `services/api/.env.example`.

## Incident Report Processor (Phase 1)
- Sample CSV: `scripts/incidents-brasaland.csv` (**100-row** grading sample).
- CLI: `scripts/analyze.py` — verified 100/96/4 and average satisfaction **3.46**.

## Incident Report Processor (Phase 2)
- Shared analysis module + FastAPI endpoints under `services/api`.
- UI: `uis/web` Incident analysis page.

## Supplier Directory
- Submission layout: `services/api/{main,models,database,seed}.py` + `routes/suppliers.py`; UI at `uis/backoffice/app/suppliers/`.
- Idempotent seeder (`uv run seed` / `python seed.py`); auto-seed on empty startup; TinyDB at `data/suppliers.json`.
- Endpoints: `POST/GET /suppliers`, `GET /suppliers/{id}`, `PATCH .../rate`, `PATCH .../status`, `DELETE /suppliers/{id}`.
- Backoffice UI: port **3101**, `/suppliers` (table with CONTEXT fields, filters, create, rate, status).
