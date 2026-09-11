# CONTEXT — Milestone 5: Backoffice inventory UI

Operations staff use the existing Brasaland backoffice (`uis/backoffice`, port **3101**) to read live `/inventory` data. Login is required (`AuthRoot` / `AuthGuard`). Copy uses **ingredient**, **delivery**, **consumption**, and **waste**. Lesson URL segments still say `products` / `inbound` / `outbound`.

## Routes

| Path | Screen |
| --- | --- |
| `/backoffice/inventory/products` | Ingredient list with computed `current_stock` |
| `/backoffice/inventory/orders/inbound` | Log a supplier delivery |
| `/backoffice/inventory/orders/outbound` | Log consumption or waste |
| `/backoffice/inventory/orders` | Read-only delivery and exit history |

Keep `/suppliers`. The extra `/backoffice` prefix is for the inventory rubric only.

## Locked UX

1. **Dropdowns, not raw IDs.** Ingredient picker shows names from `GET /inventory/products`. Supplier picker uses Carnes del Valle S.A., MiamiMeat Co., Salsas Artesanales Ltda. (plus Other). Location picker shows Brasaland kitchen labels mapped to `location_id` **1–14**.
2. **Stock colors (visual only).** `0` = empty, `0 < stock < 10` = low, `≥ 10` = healthy. The API still computes stock and still returns HTTP 400 on an over-stock exit.
3. **API client.** All HTTP lives in `lib/inventory.ts` via `@repo/auth` `authFetch` (Bearer). Components do not call `fetch`. 4xx/5xx `detail` is shown in the UI; outbound 400 is shown next to quantity.

Query `?ingredient_id=` on inbound/outbound preselects the ingredient from the list row actions.

## Env

Same FastAPI origin as suppliers. Copy `uis/backoffice/.env.example` to `.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_INVENTORY_API_URL=http://localhost:8000
```

`lib/inventory.ts` reads `NEXT_PUBLIC_INVENTORY_API_URL` first, then the shared API base.
