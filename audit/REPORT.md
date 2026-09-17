# Brasaland Lighthouse report (after)

Same native webpack `npm run dev` as the baseline. Public-site after reports are Lighthouse CLI. Backoffice after reports are signed-in Chrome DevTools on http://localhost:3101 Overview.

## Before / after

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

Both frontends now have at least one improved Lighthouse score.

Desktop backoffice SEO went 100 → 91 on the after run (likely the same invalid-dev-`robots.txt` check as the public site before `robots.ts`). Accessibility stayed 96. Best Practices stayed 100. CLS stayed 0.

## Corrections applied (real causes)

| Commit | Cause | What we did | What we did not do |
| --- | --- | --- | --- |
| `4a5a700` | Hydration delay: Overview waited on `/auth/me` | `useProtectedSession` paints when a JWT exists; `/auth/me` still runs and still 401-redirects | Did not disable Lighthouse throttling or fake a 100 |
| `8689388` | Duplicated dashboard + client shell | `getOperationsSnapshot`, one `MetricCard`, server `BackofficeShell` | Did not move Milestone 2 math out of `src/` |
| `deaa28b` | Blur header, invalid robots, eager form JS | Solid header, `robots.ts`, `BrandMark` / `VisitNotice`, `next/dynamic` on the loyalty form | Did not merge public and backoffice layouts |

Biggest public-site impact: **SEO 91 → 100** and **home mobile LCP 2.13 s → 1.75 s**. Biggest backoffice impact: **mobile Performance 40 → 45** and **TBT 6.6 s → 3.8 s**, with desktop Performance **51 → 53**.

## Refactors from the audit

- Custom hook: `useProtectedSession` in `@repo/auth`, used by `AuthGuard`.
- Shared components: `BrandMark`, `VisitNotice`, single `MetricCard`.
- Helper: `getOperationsSnapshot()` imports `src/utils/transformations` instead of duplicating calculations.

## Remaining

- `next dev` TBT stays high (webpack HMR). That is the lab environment the lesson asked for.
- Ember/cream contrast still fails one accessibility check (96).
- Desktop backoffice SEO 91 is the Next.js dev robots response; not a content/meta regression.

## Verification

- `cd packages/auth && npx jest --coverage` — 13 passed
- `cd uis/website && npm run lint && npx tsc --noEmit && npm run build` — passed
- `cd uis/backoffice && npm run lint && npx tsc --noEmit && npm run build` — passed
- After screenshots: `audit/after/backoffice-overview-desktop.png`, `audit/after/backoffice-overview-mobile.png`
