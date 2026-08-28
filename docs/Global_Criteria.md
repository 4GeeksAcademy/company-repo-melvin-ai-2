# Brasaland Identity — Global grading criteria

Single rubric for the combined authentication project. Criteria come from the **✅ What We Will Evaluate** sections of AUTH-01, AUTH-02, and AUTH-03, in that order. Every item below is required for a passing grade unless it is marked **not evaluated**.

Architecture and locked product decisions live in [`masterplan.md`](./masterplan.md). Ordered implementation steps live in [`master_instructions.md`](./master_instructions.md). This file is only the **grade sheet**.

**Sources (read in order)**

| Part | Ticket | Syllabus |
| --- | --- | --- |
| 1 | AUTH-01 | [User Authentication API](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-api/README.md) |
| 2 | AUTH-02 | [Authentication Flows in the Frontend](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-flows/README.md) |
| 3 | AUTH-03 | [Password Reset Flow](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/ai-eng-user-authentication-restore/README.md) |

**How to score**

- Mark each checkbox **Pass** or **Fail**. A part fails if any required checkbox in that part fails.
- Grade parts in order. Do not award Part 2 if Part 1 fails. Do not award Part 3 if Part 2 fails.
- Evidence: FastAPI `/docs` and curl for Part 1; internal UIs plus the public website for Part 2; API + UIs + a real inbox for Part 3.
- Secrets must never appear in git. `.env` is not evidence to commit.

**Brasaland locks that affect grading (from the masterplan)**

- One branch: `feature/brasaland-auth` (split into three PRs only if the instructor requires it).
- Canonical API: `services/api/main.py`.
- Shared UI/client: `packages/auth` (`@repo/auth`). Do not copy login/register/account three times.
- Public website `uis/website` (including `/brasa-points`) stays fully public. Brasa Points is not this User/Profile system.
- Talent Pipeline Tracker candidate data stays on the 4Geeks Playground API. Brasaland JWT is for login, guards, and profile only.
- Sprint 3 email service: **Resend** (syllabus allows Resend or SendGrid; this fork is graded on Resend).
- Seeded demo admin: Lucía Fernández (`admin`) so suppliers and incident tools can be opened without registering.

---

## Part 1 — AUTH-01: User Authentication API

Copied from the syllabus **What We Will Evaluate**. All items required.

- [ ] User CRUD is fully implemented and reachable via the API.
- [ ] Each `User` has a linked `Profile`; `name`, `phone`, and `address` are stored on `Profile`, not on `User`.
- [ ] The `role` field accepts only `admin`, `manager`, or `user`; new users created via `POST /users` default to `user`.
- [ ] Passwords are hashed at creation and compared correctly at login — plain text never touches the database.
- [ ] Login endpoint returns a valid, signed JWT token.
- [ ] `get_current_user` dependency correctly decodes the token and identifies the user.
- [ ] Protected routes return `401` when called without a valid token.
- [ ] A user accessing or updating another user's profile or credentials receives `403 Forbidden` (not only `401` for missing/invalid token).
- [ ] Token expiry and signing secret are read from environment variables, not hardcoded.
- [ ] Auth routes are under `/auth`, user routes under `/users`, and profile routes under `/profiles` — clean, consistent structure.
- [ ] At least **5 existing routes outside `/users` and `/auth`** require a valid token (in addition to the protected user/auth routes themselves).
- [ ] `User` and `Profile` remain in TinyDB after Supabase is introduced — no user tables in PostgreSQL.
- [ ] Protected monorepo routes still behave correctly when called with a valid token (no regressions).

**Not evaluated (Part 1):** Enforcing different permissions per role on every route.

**Where to verify (Brasaland)**

| Criterion | Where |
| --- | --- |
| User CRUD | `POST/GET/PUT/DELETE /users` on `services/api` |
| Profile 1:1 | TinyDB `data/auth.json`; `GET/PUT /profiles/me`; `GET /auth/me` |
| Roles | `POST /users` → `user`; only `admin` / `manager` / `user` |
| Hashing | `from passlib.hash import bcrypt` (libpass); no plaintext in TinyDB |
| Login JWT | `POST /auth/login` (`email`/`password` JSON and/or OAuth2 form for `/docs`) |
| `get_current_user` | `OAuth2PasswordBearer`; JWT `sub` = TinyDB user `id` |
| `401` / `403` | Missing/malformed/expired token → `401`; user A on user B → `403` |
| Env | `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` in gitignored `.env`; names in `.env.example` |
| Prefixes | `/auth`, `/users`, `/profiles` |
| ≥5 existing routes | All of: `GET/POST /suppliers`, `GET /suppliers/{id}`, `PATCH .../rate`, `PATCH .../status`, `DELETE /suppliers/{id}`, `POST /suppliers/admin/seed`, `POST /api/incidents/analyze`, `GET /api/incidents/results/export`. `GET /health` stays public. |
| TinyDB-only users | `services/api/data/auth.json` — never SQL/Supabase user tables |
| No regression | Lucía (or any valid token) can still list suppliers and analyze incidents |

---

## Part 2 — AUTH-02: Authentication flows in the frontend

Copied from the syllabus **What We Will Evaluate**. All items required.

- [ ] Login and registration forms work end-to-end: the token is stored after a successful call.
- [ ] Protected views redirect to `/login` when there is no valid token in storage.
- [ ] The public website (Milestone 1) continues to work without any authentication check.
- [ ] The profile view displays email from `User` and name/contact data from the linked `Profile`, and updates profile fields via `PUT /profiles/me`.
- [ ] Logout removes the token and redirects correctly.
- [ ] A `401` response from any protected API call clears the session and redirects to `/login`.

**Brasaland additions (also evaluated on this fork — locked in the masterplan / master instructions)**

- [ ] Forms live in `@repo/auth` (not three copies of login/register/account).
- [ ] Lucía can open `/suppliers` and incident analysis after login.
- [ ] Talent candidate fetches still hit Playground only (no Brasaland JWT on those calls).

**Where to verify (Brasaland)**

| Criterion | Where |
| --- | --- |
| Login / register store token | `localStorage` key `brasaland_access_token`; thin routes in backoffice, web, talent tracker |
| Guard | Client `AuthRoot` / `AuthGuard`; logged-out `/suppliers`, `/incidents`, talent home → `/login` |
| Public website | `uis/website` `/` and `/brasa-points` — no `@repo/auth`, no redirect |
| Profile | `/account/profile` — `GET /auth/me`, save via `PUT /profiles/me` |
| Logout | Clears token, `/login` |
| `401` | `authFetch` clears token and sends the browser to `/login` |
| Shared package | `packages/auth`; each internal app `file:../../packages/auth` + `transpilePackages` |
| Lucía | Backoffice `:3101/suppliers`; incident web `:3102/incidents` with Bearer |
| Playground | `uis/talent-pipeline-tracker/lib/api.ts` uses `NEXT_PUBLIC_API_URL` only |

Bearer must be sent on Brasaland calls: `uis/backoffice/lib/suppliersApi.ts`; `uis/web/src/lib/api.ts` analyze **and** export (export cannot be a bare URL).

---

## Part 3 — AUTH-03: Password reset flow

Copied from the syllabus **What We Will Evaluate**. All items required.

- [ ] `POST /auth/forgot-password` sends a real email containing the reset link when called with a registered address.
- [ ] `POST /auth/forgot-password` returns `200` even when the address is not registered — no information is leaked.
- [ ] The reset token expires after the configured window and cannot be used after expiry.
- [ ] `POST /auth/reset-password` updates the password and invalidates the token on success.
- [ ] `POST /auth/reset-password` returns `400` for expired or already-used tokens.
- [ ] `/forgot-password` shows a confirmation message after submission regardless of the result.
- [ ] `/reset-password` reads the token from the URL, submits the form, and redirects to `/login` on success.
- [ ] `/reset-password` shows a clear error with a link back to `/forgot-password` when the token is invalid or expired.
- [ ] The `/login` page has a visible "Forgot your password?" link.
- [ ] `/account/change-password` validates matching new password and confirmation, calls the API, and shows success or error feedback.
- [ ] `POST /auth/change-password` rejects wrong current passwords with `400`.
- [ ] No API keys are hardcoded — all secrets are loaded from environment variables.

**Brasaland additions (also evaluated on this fork)**

- [ ] Email is sent with **Resend** (`RESEND_API_KEY` in env; name documented in `services/api/.env.example` or `services/api/README.md`).
- [ ] Reset email includes `{PUBLIC_APP_URL}/reset-password?token=...` and is readable on mobile.
- [ ] JWT `exp` alone is not used as the only invalidation — server-side unused/expiry state (hashed token row or equivalent).

**Not evaluated (Part 3):** HTML email template; rate limiting forgot-password; audit log of resets. Verifying a custom Resend domain so Lucía’s inbox receives mail is **not** required if a real reset email was received at a registered address (Resend onboarding may only deliver to the Resend account email).

**Where to verify (Brasaland)**

| Criterion | Where |
| --- | --- |
| Real email | Registered inbox receives Resend mail with the reset link |
| Always 200 | Unknown email still `200`; same generic body; UI always confirms |
| Expiry / one-time | `RESET_TOKEN_EXPIRE_MINUTES` (15–60); second use `400`; expired `400` |
| Reset API | `POST /auth/reset-password` `{ token, new_password }` |
| Forgot UI | `/forgot-password` in each internal app; form disabled after submit |
| Reset UI | Query `token`; success → `/login` with a success message |
| Invalid token UI | Error + link to `/forgot-password` |
| Login link | “Forgot your password?” |
| Change password | Current, new, confirm; mismatch blocked client-side; wrong current → `400` |
| Secrets | `RESEND_API_KEY`, `SECRET_KEY`, seed password — env only, never git |

Forgot / reset / change-password UI lives in `@repo/auth` with thin routes in backoffice, web, and talent tracker. Not on `uis/website`.

---

## Score sheet

Count only required checkboxes (not the “not evaluated” notes).

| Part | Required items | Pass | Fail |
| --- | ---: | ---: | ---: |
| 1 AUTH-01 | 13 | | |
| 2 AUTH-02 syllabus | 6 | | |
| 2 Brasaland locks | 3 | | |
| 3 AUTH-03 syllabus | 12 | | |
| 3 Brasaland locks | 3 | | |
| **Total** | **37** | | |

**Project pass:** every required item is Pass.

**Project fail:** any required item is Fail.

---

## Out of scope (do not grade as missing)

From the masterplan, these are not Identity grading criteria:

- Role-based permissions on every route
- Merging Brasa Points with User/Profile
- Moving talent candidates off Playground
- APIs inside Next.js route handlers
- Changing root npm workspaces
- Lucía receiving Resend mail specifically (any registered inbox that actually receives the link satisfies the real-email criterion)
