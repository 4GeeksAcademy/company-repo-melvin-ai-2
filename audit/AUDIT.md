# Brasaland Lighthouse audit (before)

Measured on 17 September 2026 against native `npm run dev` (webpack) — not Docker.

- Public website: http://localhost:3000 and http://localhost:3000/brasa-points
- Backoffice Overview: http://localhost:3101 (signed-in Operations Overview)
- Chrome Lighthouse Navigation mode for the backoffice PNGs
- Lighthouse CLI (same categories) for the public site reports in `/audit/before/`

Goal: documented improvement, not a perfect 100. Do not restructure the monorepo.

## Baseline scores

| Page | Device | Performance | Accessibility | Best Practices | SEO | LCP | TBT | CLS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Backoffice `/` | Desktop | 51 | 96 | 100 | 100 | 3.9 s | 870 ms | 0 |
| Backoffice `/` | Mobile | 40 | — | — | — | 21.2 s | 6,630 ms | 0 |
| Website `/` | Desktop | 72 | 96 | 100 | 100 | 0.42 s | 916 ms | 0 |
| Website `/` | Mobile | 69 | 96 | 100 | 91 | 2.13 s | 3,926 ms | 0 |
| Website `/brasa-points` | Desktop | 74 | 96 | 100 | 100 | 0.44 s | 707 ms | 0 |
| Website `/brasa-points` | Mobile | 67 | 96 | 100 | 91 | 1.85 s | 3,159 ms | 0 |

Backoffice category scores 96 / 100 / 100 are from the Chrome four-circle report on Overview. Mobile backoffice PNG is the metrics panel only (Performance 40).

Screenshots and HTML reports: [`before/`](./before/).

## What the metrics say

### Backoffice Overview (highest pain)

First Contentful Paint is fast (0.4 s desktop, 1.0 s mobile). Largest Contentful Paint is not (3.9 s / 21.2 s). That gap is the session gate: `AuthGuard` paints “Checking your Brasaland session…” then waits for `GET /auth/me` before the Operations Overview heading and metric cards can become LCP.

Total Blocking Time (870 ms desktop, 6.6 s mobile) is the webpack Next.js client bundle hydrating `AuthRoot`, `AuthGuard`, and the `"use client"` `BackofficeShell` around the workspace. CLS is already 0.

### Public website

LCP is already acceptable on desktop. Mobile Performance is held down by main-thread work / bootup time (4–6 s) from unminified `next dev` JavaScript, plus a sticky header `backdrop-filter`. Home mobile SEO 91 is an invalid dev `robots.txt`, not missing metadata.

## Duplicated UI (at least two cases)

### 1. `MetricCard` + `OperationsDashboard`

| Copy | Path |
| --- | --- |
| Live | `uis/backoffice/components/MetricCard.tsx` |
| Live | `uis/backoffice/components/OperationsDashboard.tsx` |
| Dead duplicate | `uis/backoffice/src/components/MetricCard.tsx` |
| Dead duplicate | `uis/backoffice/src/components/OperationsDashboard.tsx` |

Both dashboards import the same Milestone 2 utilities from root `src/` and render the same four cards, location table, and top sellers. `src/app/page.tsx` also inlines the sidebar/topbar that `BackofficeShell` already owns.

**Shared extraction:** one `MetricCard`, one `getOperationsSnapshot()` helper used by the live dashboard, delete the unused `src/components` copies, and route the leftover `src/app` page through `BackofficeShell`.

### 2. Public brand mark + visit notice

| Copy | Path |
| --- | --- |
| Header wordmark | `uis/website/src/components/Header.tsx` |
| Footer wordmark | `uis/website/src/components/Footer.tsx` |
| “Online ordering coming soon” | `HomeSections.tsx` `MenuFeature` |
| Same notice | `uis/website/src/app/brasa-points/page.tsx` |

**Shared extraction:** `BrandMark` and `VisitNotice` typed components.

## Planned fixes (one issue at a time)

1. Paint the signed-in workspace as soon as a JWT exists; keep `/auth/me` in the background (LCP).
2. Extract `getOperationsSnapshot` + keep a single `MetricCard`; remove duplicated dashboard files.
3. Split `BackofficeShell` so only nav/session are client components (TBT).
4. Public site: shared `BrandMark` / `VisitNotice`, cheaper header paint, `content-visibility` below the hero, `robots.ts`, defer Brasa Points form JS.

Canonical calculations stay in root `src/`. No architecture rewrite.

## Skills

Did not install extra `skills.sh` packs. Used this repo’s delivery-verification skill plus Core Web Vitals from the Lighthouse reports (LCP, TBT, CLS).
