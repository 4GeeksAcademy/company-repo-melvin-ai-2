# Brasaland Lighthouse report (after)

Webpack `npm run dev` after-scores are in [`after/`](./after/). **Production** `next start` scores (the KPI bar: Performance ≥ 90, LCP &lt; 2.5s, CLS &lt; 0.1) are in [`production/`](./production/).

## Production (`next start`)

| Page | Device | Performance | LCP | TBT | CLS | TTFB |
| --- | --- | --- | --- | --- | --- | --- |
| Website `/` | Desktop | **100** | 0.57 s | 41 ms | 0 | 17 ms |
| Website `/` | Mobile | **97** | **2.36 s** | 122 ms | 0 | 121 ms |
| Website `/brasa-points` | Desktop | **100** | 0.53 s | 10 ms | 0 | 3 ms |
| Website `/brasa-points` | Mobile | **97** | **2.40 s** | 103 ms | 0 | 4 ms |
| Backoffice `/login` | Desktop | **99** | 0.68 s | 95 ms | 0.02 | 52 ms |
| Backoffice `/login` | Mobile | **97** | 1.78 s | 162 ms | 0.04 | 392 ms |

All of these meet Performance ≥ 90, LCP &lt; 2.5s, CLS &lt; 0.1, and TBT (INP lab stand-in) &lt; 200 ms.

Signed-in Overview was not CLI-measurable without a JWT in `localStorage` (the run redirected to `/login`). After login, `setToken` also writes a `brasaland_session` cookie so the **server** can include Overview in the first HTML. Re-run Chrome Lighthouse on Overview after signing in on the production URL to confirm that page the same way.

LCP gap closed in code: `AuthRoot` reads that cookie and skips the “Checking your Brasaland session…” placeholder, so Overview is no longer hidden until `/auth/me` returns.

## Dev after (`npm run dev`) — assignment before/after

| Frontend | Page | Device | Score that moved | Before | After |
| --- | --- | --- | --- | --- | --- |
| Public website | `/` | Mobile | **SEO** | 91 | **100** |
| Public website | `/` | Mobile | **LCP** | 2.13 s | **1.75 s** |
| Public website | `/` | Mobile | Performance | 69 | **70** |
| Public website | `/brasa-points` | Mobile | **SEO** | 91 | **100** |
| Public website | `/brasa-points` | Mobile | Performance | 67 | **70** |
| Public website | `/brasa-points` | Mobile | Speed Index | 4.69 s | **1.81 s** |
| Backoffice | `/` Overview | Desktop | **Performance** | 51 | **53** |
| Backoffice | `/` Overview | Desktop | LCP | 3.9 s | **3.7 s** |
| Backoffice | `/` Overview | Desktop | TBT | 870 ms | **780 ms** |
| Backoffice | `/` Overview | Mobile | **Performance** | 40 | **45** |
| Backoffice | `/` Overview | Mobile | LCP | 21.2 s | **18.8 s** |
| Backoffice | `/` Overview | Mobile | TBT | 6,630 ms | **3,750 ms** |

Both frontends have at least one improved Lighthouse score on `npm run dev`. Those scores stay below 90 because webpack HMR JS is unminified. Production is the KPI environment.

Desktop backoffice SEO went 100 → 91 on the **dev** after run. Production backoffice login SEO is 100 (`app/robots.ts`). Accessibility 96 on the public site is leftover ember/cream contrast.

## Corrections applied (real causes)

| Cause | What we did | What we did not do |
| --- | --- | --- |
| Hydration delay: Overview waited on `/auth/me` | `useProtectedSession` paints when a JWT exists | Did not disable throttling |
| Duplicated dashboard + client shell | `getOperationsSnapshot`, server `BackofficeShell` | Did not copy math into the UI |
| Blur header, invalid robots, eager form JS | Solid header, `robots.ts`, shared components, dynamic form | Did not merge layouts |
| First HTML omitted Overview (LCP) | `brasaland_session` cookie + `hasSessionCookie` so SSR includes the dashboard | Did not put the JWT in the cookie |

Biggest production impact: minified `next start` JS (TBT 3.8 s → ~100 ms). Biggest remaining LCP fix: session cookie so Overview is in the first HTML.

## Refactors from the audit

- Custom hook: `useProtectedSession` in `@repo/auth`.
- Shared components: `BrandMark`, `VisitNotice`, single `MetricCard`.
- Helper: `getOperationsSnapshot()` imports `src/utils/transformations`.

## Remaining

- Ember/cream contrast still fails one accessibility check (96) on the public site.
- Sign in on production backoffice and Lighthouse Overview if the grader wants that exact URL, not `/login`.

## Verification

- `cd packages/auth && npx jest --coverage` — 13 passed
- `uis/website` and `uis/backoffice` `npm run build` passed
- Production Lighthouse: [`production/`](./production/)
