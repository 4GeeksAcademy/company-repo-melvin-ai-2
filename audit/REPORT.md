# Brasaland Lighthouse report (after)

Re-measured on 17 September 2026 with the same native webpack `npm run dev` servers as the baseline. Public-site after reports are Lighthouse CLI (same categories as before). Backoffice after still needs a signed-in Chrome pass on http://localhost:3101 — drop those PNGs in this folder.

Full HTML reports: [`after/`](./after/). Baseline: [`AUDIT.md`](./AUDIT.md) and [`before/`](./before/).

## Score comparison

| Page | Device | Perf before → after | SEO before → after | LCP before → after | Notes |
| --- | --- | --- | --- | --- | --- |
| Website `/` | Mobile | 69 → **70** | 91 → **100** | 2.13 s → **1.75 s** | Speed Index 1.80 s → 1.39 s. TBT still ~3.5 s in `next dev`. |
| Website `/` | Desktop | 72 → 72 | 100 → 100 | 0.42 s → 0.44 s | Stable. Remaining TBT is the webpack runtime. |
| Website `/brasa-points` | Mobile | 67 → **70** | 91 → **100** | 1.85 s → 1.99 s | Speed Index 4.69 s → **1.81 s**. |
| Website `/brasa-points` | Desktop | 74 → 74 | 100 → 100 | 0.44 s → 0.43 s | Stable. |
| Backoffice `/` | Desktop | 51 (LCP 3.9 s) | 100 | pending Chrome | Auth no longer blocks paint on `/auth/me`. Re-run Lighthouse while signed in. |
| Backoffice `/` | Mobile | 40 (LCP 21.2 s) | — | pending Chrome | Same. |

Accessibility stayed **96** (ember-on-cream contrast). Best Practices stayed **100**. CLS stayed **0**.

## What changed

1. **LCP (backoffice)** — `useProtectedSession` paints Overview as soon as a JWT is in `localStorage`. `GET /auth/me` still runs and still sends 401s to `/login`.
2. **Duplication** — one `MetricCard`, `getOperationsSnapshot()` for the live dashboard, deleted unused `uis/backoffice/src/components` copies, leftover `src/app` page now uses `BackofficeShell`. Public site gained `BrandMark` and `VisitNotice`.
3. **Client JS (backoffice)** — `BackofficeShell` is a server component; only `BackofficeNav` and `SessionNav` hydrate.
4. **Public site paint** — solid header (no `backdrop-filter`), `content-visibility` below the hero, cheaper grill-card shadow, `robots.ts` (SEO 91 → 100), Brasa Points form loaded with `next/dynamic`.

Canonical Milestone 2 math is still imported from root `src/`. Layouts were not merged.

## Remaining (on purpose)

- `npm run dev` Total Blocking Time will stay high because webpack HMR and unminified React hydrate on every audit. A production `next start` run would show a larger Performance jump; the lesson asked for native `npm run dev` scores.
- Accessibility 96: eyebrow/ember contrast on cream.
- Backoffice after screenshots: sign in on http://localhost:3101, Desktop then Mobile Lighthouse, save PNGs next to the public-site after reports.

## Verification

- `cd packages/auth && npx jest --coverage` — **13 passed**
- `cd uis/website && npm run lint && npx tsc --noEmit && npm run build` — passed (`/`, `/brasa-points`, `/robots.txt`)
- `cd uis/backoffice && npm run lint && npx tsc --noEmit && npm run build` — passed (`/`, `/suppliers`, inventory routes)
