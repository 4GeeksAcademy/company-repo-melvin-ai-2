# Brasaland caching report

Branch `feature/caching-optimisation`. Frontend is `uis/backoffice`. Backend is `services/api/main.py`. No Redis in this stack, so catalog reads use an in-memory TTL dictionary (`app/cache.py`).

## Frontend decisions

| Component / route | Technique | Why defer or memoize | Benefit |
| --- | --- | --- | --- |
| `/backoffice/inventory/orders/inbound` | `next/dynamic` on `InboundDeliveryForm` | The form is client-only (dropdowns, stock lookup, submit). Overview does not use it. Loading it with the first backoffice JS would delay the dashboard. | Form JS loads on that route, with a status message while the chunk arrives. |
| `/backoffice/inventory/orders/outbound` | `next/dynamic` on `OutboundExitForm` | Same split. Consumption and waste validation is not needed to paint Overview. | Same as inbound. |
| Overview `OperationsDashboard` | `useMemo` around `getOperationsSnapshot()` | The helper ranks 14 locations, margins, waste cost, and top items from the Milestone 2 sample. Re-running that on every Overview render repeats work whose inputs do not change during the session. | One calculation per change of `sales`, `locations`, `menuItems`, or `wasteRecords`. |

Dependency array: `[sales, locations, menuItems, wasteRecords]`. Those are the component inputs. Defaults are the Milestone 2 sample arrays. The snapshot recomputes only when a caller passes a different list.

Public `/brasa-points` already lazy-loads `LoyaltyForm` from the Lighthouse work. It is not a new decision on this branch.

## Backend decisions

Timing middleware logs one line per request: `METHOD path status milliseconds`. That is how a route is judged before it is cached.

| Endpoint | Cost | How often | How often the data changes | TTL | Invalidation |
| --- | --- | --- | --- | --- | --- |
| `GET /inventory/products` | Sums every delivery and exit to compute `current_stock` for each SKU | Every ingredients screen and both inventory forms | Only when a SKU is created or a delivery / consumption / waste row is written | 60 seconds | `invalidate_product_catalog()` after those writes |
| `GET /suppliers` | Reads the full TinyDB directory (filters included) | Every supplier screen load | Only when a supplier is created, rated, suspended, deleted, or re-seeded | 60 seconds | `invalidate_supplier_catalog()` after those writes |

Cache keys are the query filters only (`country`, `category`). They do **not** include the Bearer user. Both payloads are the same for every signed-in operator. Stock is chain-wide, not per person.

`GET /auth/me` was checked live in tests: Lucía and Carlos receive different emails, and nothing is stored under an auth cache key.

## Tradeoff (freshness vs speed)

A 60-second TTL can show stock or a supplier rate that a write already changed **if that write forgot to clear the prefix**. The TTL is only a backstop. The real freshness rule is delete-on-write, so a delivery updates the ingredients list on the next GET. Sixty seconds of possible staleness is acceptable for a missed invalidation. Caching with no expiry would not be: a kitchen could log waste and still see the old stock until the process restarts.

## What was not cached, and why

`GET /auth/me`, `GET /users`, and `GET /profiles/me` were not cached. They are session-specific. A shared key would return one operator’s email and role to another. `GET /inventory/orders` was not cached either: each row carries `user_uuid`, and the history changes on every delivery. The hot repeated reads are the ingredient list and the supplier directory, not the order log.

`POST` routes are not cached. They change data.

## Verification

- `uv run pytest` — 54 passed, then `test_product_list_skips_stock_math_until_outbound` passed. `tests/test_cache.py` covers TTL expiry, supplier list hitting TinyDB once until a create, and `/auth/me` staying out of the catalog cache.
- That inventory test: the ingredient list skips stock math on the second GET, then a consumption write clears the cache and the next GET shows stock down by 1.
- `cd uis/backoffice && npx tsc --noEmit` passed. ESLint on `OperationsDashboard.tsx` passed with no dependency-array warning.
- `cd uis/backoffice && npm run build` passed (Next.js 16.2.11). Routes include `/`, `/backoffice/inventory/orders/inbound`, and `/backoffice/inventory/orders/outbound`.
- Production server on port 3199, with cookie `brasaland_session=1`: Overview HTML includes “Recorded revenue”, “Performance snapshot”, and “Top sellers”. Inbound HTML includes “Log a supplier delivery”. Outbound HTML includes “Log consumption or waste”. Overview HTML does not include those form headings. Without the cookie, `/` shows “Checking your Brasaland session…”.
