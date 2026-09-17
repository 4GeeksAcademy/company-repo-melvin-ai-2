# Brasaland Lighthouse audit (before)

Measured on 17 September 2026 against native `npm run dev` (webpack) — not Docker. Public site: http://localhost:3000 and `/brasa-points`. Backoffice: signed-in Operations Overview at http://localhost:3101.

This file is the **before** analysis. Fixes and after scores are in [`REPORT.md`](./REPORT.md). Goal: documented improvement, not a 100. No architecture rewrite.

## Baseline scores

| Page | Device | Performance | Accessibility | Best Practices | SEO | LCP | TBT | CLS | TTFB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Backoffice `/` | Desktop | **51** | **96** | **100** | **100** | **3.9 s** | 870 ms | 0 | — |
| Backoffice `/` | Mobile | **40** | (same report family) | (same) | (same) | **21.2 s** | 6,630 ms | 0 | — |
| Website `/` | Desktop | 72 | 96 | 100 | 100 | 0.42 s | 916 ms | 0 | 0.39 s |
| Website `/` | Mobile | 69 | 96 | 100 | **91** | 2.13 s | 3,926 ms | 0 | 0.30 s |
| Website `/brasa-points` | Desktop | 74 | 96 | 100 | 100 | 0.44 s | 707 ms | 0 | 0.07 s |
| Website `/brasa-points` | Mobile | 67 | 96 | 100 | 91 | 1.85 s | 3,159 ms | 0 | 2.91 s |

Backoffice PNGs are Chrome DevTools (Navigation). Public-site reports are Lighthouse CLI with the same four categories. Evidence: [`before/`](./before/).

INP did not appear as a numeric lab value on these Navigation reports (no long interaction during the audit). TBT is the lab stand-in for main-thread / hydration cost.

## Root causes (KPIs first, not a dump of Lighthouse tips)

Lighthouse flags are symptoms. These are the code reasons.

### 1. Backoffice LCP — session gate hides Overview (hydration)

**KPI:** LCP 3.9 s desktop / 21.2 s mobile. FCP is already fast (0.4 s / 1.0 s). CLS is 0.

**Cause:** `AuthGuard` set `ready` only after `GET /auth/me` succeeded. The first paint was “Checking your Brasaland session…”. The LCP element (Overview `h1` + metric cards) could not exist until that network round trip finished. That is a **hydration / render-delay** issue, not missing image compression (this page has no hero bitmap).

**Not the cause:** layout shift (CLS 0), unoptimized photos, or a missing `priority` on `next/image`.

### 2. Backoffice TBT — whole shell was a client component

**KPI:** TBT 870 ms desktop / 6.6 s mobile (dev webpack, unminified).

**Cause:** `BackofficeShell` was `"use client"`, so the sidebar, topbar, and workspace chrome all hydrated even though only `usePathname()` and `SessionNav` need the browser. `AuthRoot` still has to hydrate; we cannot delete auth. We can stop wrapping the dashboard chrome in an extra client boundary.

### 3. Public SEO 91 — invalid dev `robots.txt`

**KPI:** Home and Brasa Points mobile SEO 91.

**Cause:** Next.js `npm run dev` serves a robots response Lighthouse rejects. The site already had metadata and JSON-LD. Adding `src/app/robots.ts` is the real fix for that audit, not hiding the category.

### 4. Public LCP / main-thread — expensive header paint + large client form

**KPI:** Home mobile LCP 2.13 s; Brasa Points TBT 3.2 s; Speed Index on Brasa Points mobile 4.69 s.

**Cause:** sticky header used `backdrop-filter: blur(14px)` on every scroll frame’s compositor work; `.grill-card` used a heavy shadow. `/brasa-points` eagerly loaded the full `LoyaltyForm` client module. `next dev` JS stays unminified — that TBT will not hit 0 in lab on webpack HMR, so we do not “fix” it by disabling throttling.

## Duplicated UI (two cases)

### Case A — operations cards and dashboard

| Copy | Path | Why it qualifies |
| --- | --- | --- |
| Live | `uis/backoffice/components/MetricCard.tsx` | Canonical card |
| Live | `uis/backoffice/components/OperationsDashboard.tsx` | Canonical dashboard |
| Dead duplicate | `uis/backoffice/src/components/MetricCard.tsx` | Same props, same markup |
| Dead duplicate | `uis/backoffice/src/components/OperationsDashboard.tsx` | Same `src/` imports and table |
| Inlined chrome | `uis/backoffice/src/app/page.tsx` | Repeated sidebar/topbar instead of `BackofficeShell` |

**Shared abstraction:** one `MetricCard`, one `getOperationsSnapshot()` helper (calls canonical `src/utils`, does not copy math), delete unused `src/components` files, leftover page uses `BackofficeShell`.

### Case B — public wordmark and visit notice

| Copy | Path |
| --- | --- |
| Header wordmark | `uis/website/src/components/Header.tsx` |
| Footer wordmark | `uis/website/src/components/Footer.tsx` |
| “Online ordering coming soon” | `HomeSections.tsx` `MenuFeature` |
| Same notice | `uis/website/src/app/brasa-points/page.tsx` |

**Shared abstraction:** typed `BrandMark` and `VisitNotice`.

## Planned fixes (one KPI per change)

1. Paint Overview as soon as a JWT exists (`useProtectedSession`) — **LCP / hydration**.
2. Extract snapshot + single `MetricCard`; remove duplicates — **refactor from code analysis**.
3. Server `BackofficeShell`, client `BackofficeNav` only — **TBT / hydration**.
4. `BrandMark` / `VisitNotice`, solid header, `robots.ts`, dynamic Brasa Points form — **LCP / SEO / JS**.

## Agent skills

Did **not** install the optional skills.sh packs. Lighthouse lab reports already named the failing KPIs (LCP, TBT, CLS). Installing extra skills would not have changed the diagnosis. The work followed the Core Web Vitals order those skills describe: measure → fix one cause → remeasure. Evidence of that workflow is this file plus [`REPORT.md`](./REPORT.md), not a skills.sh folder.
