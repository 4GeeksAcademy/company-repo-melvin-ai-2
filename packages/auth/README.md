# `@repo/auth`

Shared Brasaland authentication for internal Next.js apps. Do not copy login/register/account into each UI.

## Public API

- `AuthRoot` — provider + client guard (skips `/login`, `/register`, `/forgot-password`, `/reset-password`)
- `AUTH_PUBLIC_PATHS` — those public pathnames
- `LoginForm`, `RegisterForm`, `ProfileForm`, `ForgotPasswordForm`, `ResetPasswordForm`, `ChangePasswordForm`
- `SessionNav` — profile, change-password, logout
- `getToken` / `setToken` / `clearToken`
- `authFetch` — Brasaland API calls with `Authorization: Bearer`
- `ErrorBanner` — human-readable error with retry, home, and support contact

## Consume

In each internal app `package.json`:

```json
"@repo/auth": "file:../../packages/auth"
```

In `next.config`:

```ts
transpilePackages: ["@repo/auth"]
```

Set `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`) for the Brasaland API. Talent Pipeline Tracker keeps `NEXT_PUBLIC_API_URL` for the 4Geeks Playground candidate API and must not send this JWT there.

The public website (`uis/website`) does not import this package.
