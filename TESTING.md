# Brasaland authentication test suite (AUTH-088)

A prior refactor broke JWT expiration because the identity API had no automated checks. This suite locks the **decisions** the authentication module makes (who is created, who receives a session, when a token is dead, when a reset is consumed) rather than HTTP serialization, CORS, OpenAPI, or FastAPI’s 422 JSON layout.

API-042 (supplier / incident backoffice tests) is out of scope on this branch.

## How to run

From the **git repository root** (the grader command):

```bash
uv sync --group dev
uv run pytest
uv run pytest --cov
```

`uv run pytest --cov` measures the authentication package `app.auth` and fails if coverage is below **70%**. The FastAPI app remains a standalone project under `services/api`; `cd services/api && uv run pytest` still works.

TypeScript helpers live in `@repo/auth`:

```bash
cd packages/auth
npm install
npx jest --coverage
```

Tests use a temporary TinyDB, a test `SECRET_KEY`, and a mocked Resend client. They never write Lucía’s real `data/auth.json` or send mail.

## Coverage results

Recorded **2026-08-31** from the git root (`uv run pytest --cov`):

| Command | Result |
| --- | --- |
| `uv run pytest` | **44 passed** |
| `uv run pytest --cov` | **44 passed**, `app.auth` coverage **83%** (gate 70%) |
| `cd packages/auth && npx jest --coverage` | **10 passed** |

Line coverage on `app.auth` is 83%, not 100%. Untouched lines are Resend send internals, seed CLI `main`, and TinyDB disk-error paths. Those are not auth *decisions*; the cases above cover login, expiry, reset consume-once, and privilege checks.

## AI-assisted workflow

Cases the AI test-plan pass added (reviewed before they were written):

1. **Expired JWT is rejected** (`test_expired_token_is_rejected`) — AUTH-088’s original bug: expiration existed in `tokens.py` but had no test. The suite asserts `user_id_from_token` raises when `exp` is in the past, not merely that FastAPI returns 401.
2. **Unknown email on forgot-password mints no reset row** (`test_forgot_password_unknown_email_does_not_mint_a_reset`) — AI-suggested account-enumeration edge: the HTTP body still looks successful, so the assertion is “no `password_resets` row,” not a status code.

No production auth bug was found while running the suite. If a later run fails a decision assert, fix the API and record it here.

## What each suite covers

| Suite | What it decides |
| --- | --- |
| `services/api/tests/test_register.py` | Public registration creates a `user` with a linked profile, and refuses duplicates / empty credentials. |
| `services/api/tests/test_login.py` | Valid Brasaland credentials issue a JWT; inactive and wrong passwords do not. |
| `services/api/tests/test_token.py` | Access tokens carry `sub` + future `exp`; expired and malformed tokens are invalid. |
| `services/api/tests/test_me.py` | A live session returns email, role, and profile; missing or garbage Bearer is unauthenticated. |
| `services/api/tests/test_forgot_password.py` | Known active emails mint a one-time reset; unknown emails and mail failures do not leak accounts. |
| `services/api/tests/test_reset_password.py` | A valid reset token changes the password once; expired / reused tokens do not. |
| `services/api/tests/test_change_password.py` | An authenticated operator can rotate their password only with the current password. |
| `services/api/tests/test_users.py` | Self-or-admin access, role changes reserved to admin, missing users not found. |
| `services/api/tests/test_profiles.py` | The signed-in operator can read and patch their own profile. |
| `services/api/tests/test_passwords.py` | bcrypt hash/verify for Brasaland credentials. |
| `services/api/tests/test_mail.py` | Reset links use `PUBLIC_APP_URL`; missing Resend key skips send. |
| `services/api/tests/test_seed.py` | Lucía is seeded once as `admin` when credentials exist, and skipped when they do not. |
| `packages/auth/*.test.ts` | Token storage and human error mapping in `@repo/auth` (JWT create/verify stays in Python). |

## Intended cases (written before the tests)

Each authentication endpoint has at least one happy path, one edge case, and one failure mode. Cases use Brasaland operators (Lucía Fernández as admin, a restaurant operator as `user`).

### `POST /users` (register)

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Register `carlos.restrepo@brasaland.com` → a `user` row exists with a linked profile, role is not `admin`. | Public signup must create a normal operator, never an admin. |
| Edge | Register the same email twice → still a single user row. | Duplicate emails are the classic identity bug. |
| Failure | Empty email/password → no user is stored. | Incomplete signup must not create a credential. |

### `POST /auth/login`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Lucía’s email + password → an access token whose `sub` is her user id. | Session issue is the core login decision. |
| Edge | Inactive operator with the correct password → no token. | Disabled accounts must not sign in. |
| Failure | Wrong password → no token. | Invalid credentials must not mint a session. |

### Access tokens (`create_access_token` / `user_id_from_token`)

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Fresh token decodes to the same user id and `exp` is in the future. | Sessions must expire; `exp` is the contract. |
| Edge | Empty or unsigned garbage is invalid. | Malformed Bearer values must not identify anyone. |
| Failure | Token whose `exp` is in the past is rejected. | This is the AUTH-088 regression (expiration was previously untested). |

### `GET /auth/me`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Bearer session returns that operator’s email, role, and profile name. | The session identity the UIs trust. |
| Edge | Request with no Authorization header → not authenticated. | Missing token is not a session. |
| Failure | Malformed JWT → not authenticated. | Garbage tokens must not become Lucía (or anyone). |

### `POST /auth/forgot-password`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Known active email (mail mocked) → a hashed reset row exists for that user. | Recovery must mint a one-time token. |
| Edge | Unknown email → success with **no** reset row. | Do not reveal whether an address is registered. |
| Failure | Resend raises `MailSendError` → still succeeds; the caller learns nothing about mail or accounts. | Mail outages must not enumerate users or leak internals. |

### `POST /auth/reset-password`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Valid raw token → password hash changes and the token is marked used. | Recovery must actually rotate the credential. |
| Edge | Same token submitted again → password stays as after the first reset. | One-time use. |
| Failure | Expired or random token → password unchanged. | Dead links must not open the account. |

### `POST /auth/change-password`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Correct current password → stored hash matches the new password. | Signed-in operators can rotate credentials. |
| Edge | Wrong current password → hash unchanged. | Must prove they already know the password. |
| Failure | No Bearer token → hash unchanged. | Password change is an authenticated action. |

### `GET /users`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Authenticated operator sees registered Brasaland emails. | Directory listing for internal tools. |
| Edge | Only one operator exists → list length is 1. | Empty-ish directory still returns that session’s user. |
| Failure | No token → no user list is returned. | The user directory is not public. |

### `GET /users/{id}`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Operator reads their own id. | Self-service. |
| Edge | Admin (Lucía) reads another operator. | Admin support path. |
| Failure | Operator reads someone else’s id → not allowed; or missing id is not found. | Authorization and existence. |

### `PUT /users/{id}`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Operator updates their own email. | Self-service identity. |
| Edge | Non-admin tries to set `role=admin` → role stays `user`. | Privilege escalation. |
| Failure | Operator updates another user → not allowed. | Cannot edit a coworker’s account. |

### `DELETE /users/{id}`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Operator deletes their own account → user row is gone. | Self-service removal. |
| Edge | Admin deletes another operator → that user is gone. | Admin cleanup. |
| Failure | Operator deletes someone else → the other user still exists. | Cannot remove a coworker. |

### `GET /profiles/me` and `PUT /profiles/me`

| Kind | Case | Why |
| --- | --- | --- |
| Happy | Signed-in operator reads and then updates name/phone/address. | Profile is 1:1 with the user. |
| Edge | Partial PUT leaves unspecified fields as they were. | Patch semantics. |
| Failure | No token → profile is not returned or changed. | Profile is not public. |

## TypeScript (`@repo/auth`)

Token generation, JWT validation, and password hashing are Python. Jest covers client utilities only.

| Function | Happy | Failure |
| --- | --- | --- |
| `setToken` / `getToken` / `hasToken` / `clearToken` | Store then read the Brasaland access token. | `clearToken` / missing key → no session token. |
| `parseApiError` | Human `detail` string is used. | Traceback-like `detail` is replaced with the fallback. |
| `messageForHttpStatus` | 401 / 403 / 404 map to sign-in, permission, and not-found copy. | Unknown 4xx keeps the fallback. |
| `fieldErrorsFromApi` | `loc`/`msg` list maps to field names. | Non-array or empty payload → no fields. |
| `getBrasalandApiBase` | Env base URL without a trailing slash. | Unset env → `http://localhost:8000`. |

## Bugs found in this suite

None. The expired-token case guards a regression that was already fixed in production; the test did not need a new API change.
