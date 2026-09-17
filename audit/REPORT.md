# Brasaland Lighthouse report (after)

Same native webpack `npm run dev` as the baseline. Public-site after reports are Lighthouse CLI. Backoffice after still needs signed-in Chrome PNGs on http://localhost:3101 (see question at the end of this delivery).

## Before / after

| Frontend | Page | Device | Score that moved | Before | After |
| --- | --- | --- | --- | --- | --- |
| Public website | `/` | Mobile | **SEO** | 91 | **100** |
| Public website | `/` | Mobile | **LCP** | 2.13 s | **1.75 s** |
| Public website | `/` | Mobile | Performance | 69 | **70** |
| Public website | `/brasa-points` | Mobile | **SEO** | 91 | **100** |
| Public website | `/brasa-points` | Mobile | Performance | 67 | **70** |
| Public website | `/brasa-points` | Mobile | Speed Index | 4.69 s | **1.81 s** |
| Backoffice | `/` Overview | Desktop | Performance / LCP | 51 / 3.9 s | **pending Chrome after PNG** |
| Backoffice | `/` Overview | Mobile | Performance / LCP | 40 / 21.2 s | **pending Chrome after PNG** |

Accessibility stayed 96 (ember-on-cream contrast). Best Practices stayed 100. CLS stayed 0.

The grading rule is **at least one Lighthouse score per frontend**. The website already meets that (SEO and LCP). The backoffice does not until Overview is measured again while signed in.

## Corrections applied (real causes)

| Commit | Cause | What we did | What we did not do |
| --- | --- | --- | --- |
| `4a5a700` | Hydration delay: Overview waited on `/auth/me` | `useProtectedSession` paints when a JWT exists; `/auth/me` still runs and still 401-redirects | Did not disable Lighthouse throttling or fake a 100 |
| `8689388` | Duplicated dashboard + client shell | `getOperationsSnapshot`, one `MetricCard`, server `BackofficeShell` | Did not move Milestone 2 math out of `src/` |
| `deaa28b` | Blur header, invalid robots, eager form JS | Solid header, `robots.ts`, `BrandMark` / `VisitNotice`, `next/dynamic` on the loyalty form | Did not merge public and backoffice layouts |

Biggest public-site impact: **SEO 91 → 100** from a real `robots.txt`, plus **home mobile LCP 2.13 s → 1.75 s** from cheaper first paint. Biggest intended backoffice impact: LCP no longer gated on `/auth/me` (must be confirmed with after screenshots).

## Refactors from the audit

- Custom hook: `useProtectedSession` in `@repo/auth`, used by `AuthGuard`.
- Shared components: `BrandMark`, `VisitNotice`, single `MetricCard`.
- Helper: `getOperationsSnapshot()` imports `src/utils/transformations` instead of duplicating calculations.

## Remaining

- `next dev` TBT stays high (webpack HMR). That is the lab environment the lesson asked for.
- Ember/cream contrast still fails one accessibility check (96).
- **Need:** Chrome Lighthouse after PNGs for signed-in Overview, Desktop and Mobile, saved as `audit/after/backoffice-overview-desktop.png` and `audit/after/backoffice-overview-mobile.png`.

## Verification

- `cd packages/auth && npx jest --coverage` — 13 passed
- `cd uis/website && npm run lint && npx tsc --noEmit && npm run build` — passed
- `cd uis/backoffice && npm run lint && npx tsc --noEmit && npm run build` — passed
