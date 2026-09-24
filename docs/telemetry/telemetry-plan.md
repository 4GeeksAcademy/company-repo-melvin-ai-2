# Brasaland telemetry plan

Design only. Do not emit events from the API or the backoffice in this phase. Another developer should be able to instrument from this file and from [`event-schemas.json`](event-schemas.json) without asking how a field is spelled.

Company brief, copied exactly for the mandatory floor: [`CONTEXT-company.md`](CONTEXT-company.md).

`schemaVersion` for every event in this plan is `"1.0.0"`.

## Envelope

Every event, mandatory or not, is one JSON object. Keys outside this list are rejected.

| Field | Type | Rule |
| --- | --- | --- |
| `eventId` | UUID string | New id per emit. Not the order id. |
| `timestamp` | string, ISO 8601 date-time | UTC, with offset. Example: `2026-09-23T22:15:00Z`. |
| `sessionId` | string | Backoffice session id. For a failed login before a session exists, use `"none"`. |
| `userId` | string or null | Opaque operator id already stored as `user_uuid` (TinyDB id as a string). Never an email, name, or JWT. `null` only when no account was resolved. |
| `event_type` | string | `entity_action`, snake_case, from the catalogue below. |
| `schemaVersion` | string | `"1.0.0"`. |
| `requestId` | string | Same id on the HTTP request and on every event that request caused, so a delivery and a threshold alert can be joined. |
| `properties` | object | Allowlist per event. `additionalProperties` is false. |

`userId` is an identifier, not a name. Employee names, customer names, emails, passwords, tokens, and free-text form values are not properties.

## Phase 1 — Catalogue

Classification is `mandatory` when the row is in `CONTEXT-company.md`, and `identified` when this plan adds it. Discard a row that cannot finish the sentence.

### Mandatory (CONTEXT floor)

These six names, hypotheses, and decisions are the brief. Do not rename them.

| `event_type` | Class | We capture it because we need to know… | …which allows us to decide… |
| --- | --- | --- | --- |
| `inbound_order_created` | mandatory | how much of which product each location buys, and from which supplier | whether Lucía should consolidate purchasing and negotiate price |
| `outbound_order_created` | mandatory | which products each location consumes for dish preparation, and how fast | whether Felipe should change the suggested supplier reorder |
| `stock_waste_registered` | mandatory | how much is lost, why (`expired`, `kitchen_error`, `theft_suspected`), and at which location | which locations Felipe audits first |
| `stock_threshold_triggered` | mandatory | how often a location falls below the configured minimum for a product | whether to raise that minimum or shorten replenishment |
| `direct_stock_edit_rejected` | mandatory | whether staff try to change stock outside an inbound or outbound order | where Jake schedules traceability training or tighter permissions |
| `ingredient_price_variance_detected` | mandatory | when a product/supplier unit cost moves more than 10% from the historical unit cost | whether Lucía and Mariana renegotiate or switch supplier |

### Inventory flow and the five required instrumentation points

Authenticated operator opens the backoffice, then logs a delivery or an exit. Instrument at least these points:

1. `inbound_order_created` after `POST /inventory/orders/inbound` commits.
2. `outbound_order_created` after `POST /inventory/orders/outbound` commits with preparation consumption.
3. `stock_waste_registered` after that same outbound route commits a waste exit. The live API still stores one reason, `waste`. The instrumenter must not emit this event until the client sends `expired`, `kitchen_error`, or `theft_suspected`. Mapping every waste row to one of those three would invent a cause.
4. `direct_stock_edit_rejected` when a client sends `current_stock` (or any stock column) on create or update. The table has no stock column. Reject the write and emit this event. There is no successful direct-edit event.
5. `inventory_order_validation_failed` on HTTP 400 (quantity above derived stock) and HTTP 422 (bad unit, category, country, or reason).
6. `stock_threshold_triggered` when derived stock at that `location_id` is strictly below the configured minimum after a successful inbound or outbound commit.

The backoffice paints “low” when stock is under 10. That badge is visual only. The configured minimum for `stock_threshold_triggered` is a per-product, per-location number supplied at instrumentation time, not the badge cutoff, unless operations explicitly sets the minimum to 10.

### Identified opportunities

At least three categories: inventory, authentication, errors, performance, navigation.

| `event_type` | Category | Class | We capture it because we need to know… | …which allows us to decide… |
| --- | --- | --- | --- | --- |
| `inventory_order_validation_failed` | errors | identified | which products and locations hit rejected deliveries or exits | whether the form, the minimum, or training is wrong |
| `stock_threshold_edit_rejected` | inventory | identified | whether operators try to change the minimum alert themselves | whether that control stays with Felipe or opens for managers |
| `auth_login_failed` | authentication | identified | how many sign-in attempts fail per day, without storing the address they typed | whether Jake investigates a lockout or a credential attack |
| `auth_login_succeeded` | authentication | identified | how many operator sessions actually start | whether a spike in failures is noise or a real outage |
| `auth_session_expired` | authentication | identified | how often a half-finished backoffice task dies on an expired token | whether to lengthen the token or save drafts |
| `api_latency_recorded` | performance | identified | which inventory and auth routes are slow for kitchen staff | which route to fix before a Friday service |
| `backoffice_page_viewed` | navigation | identified | which backoffice sections operators open | which screens are still black boxes |
| `backoffice_flow_abandoned` | navigation | identified | which delivery or waste flows stop before submit | which form to shorten |
| `client_error_uncaught` | errors | identified | which routes throw in the browser | which page to patch before trusting its counts |

## Phase 2 — Schemas

The allowlist is [`event-schemas.json`](event-schemas.json) (JSON Schema 2019-09). A key not listed for that `event_type` is dropped, not stored. The tables below match that file.

Shared inventory properties, required on every mandatory inventory event:

| Property | Type | Required | Description | Sensitive |
| --- | --- | --- | --- | --- |
| `location_id` | integer 1–14 | yes | Backoffice location id | no |
| `country` | `CO` or `US` | yes | Location country. Not the UI language. | no |
| `product_id` | integer | yes | Ingredient id | no |
| `product_category` | string enum | yes | `protein`, `vegetable`, `sauce`, `beverage`, `packaging`, `cleaning` | no |
| `quantity` | number > 0, except threshold and rejection events where it is the stock or attempted stock (≥ 0) | yes | See each event | no |
| `unit` | `kg`, `liter`, or `unit` | yes | Live API spells litre `litre`. Emit `liter`. | no |
| `currency` | `COP` or `USD` | yes | Colombia `COP`, Florida `USD`. Do not convert. | no |

Category map from the live ingredient row: `meat` → `protein`, `produce` → `vegetable`. Other live categories already match.

`userId` can identify an employee. It stays the opaque id. Do not add `email`, `name`, or `manager` beside it.

### `inbound_order_created`

A committed supplier delivery.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| shared inventory fields | | yes | `quantity` is the quantity received |
| `supplier_id` | string | yes | Supplier directory id. Resolve today’s `supplier_name` to that id. If it does not match, use `"unmatched"` and do not copy the typed name. |
| `unit_cost` | number ≥ 0 | yes | Unit cost in `currency`. Required so price variance has a history. |
| `order_id` | integer | yes | `IngredientEntry.id` |

### `outbound_order_created`

Committed consumption for dish preparation. Not waste.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| shared inventory fields | | yes | `quantity` is the quantity consumed |
| `reason` | const `preparation` | yes | Only this value. Live API `consumption` maps here. |
| `order_id` | integer | yes | `IngredientExit.id` |

### `stock_waste_registered`

Committed waste. `reason` is required and is only `expired`, `kitchen_error`, or `theft_suspected`.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| shared inventory fields | | yes | `quantity` is the quantity lost |
| `reason` | enum of those three | yes | Do not emit `waste`. |
| `order_id` | integer | yes | `IngredientExit.id` |

### `stock_threshold_triggered`

Derived stock for that product at that location is now strictly below the configured minimum. Emit once per crossing, not on every later read while it stays below.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| shared inventory fields | | yes | `quantity` is stock after the order (≥ 0) |
| `threshold_quantity` | number ≥ 0 | yes | Configured minimum in `unit` |
| `triggering_order_id` | integer | yes | Entry or exit that caused the crossing |

Live `current_stock` is chain-wide. The instrumenter must compute stock for `location_id` from entries and exits at that location. Do not compare the chain-wide total to a location minimum.

### `direct_stock_edit_rejected`

Rejected attempt to write stock outside an order.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| shared inventory fields | | yes | `quantity` is the attempted stock (≥ 0) |
| `rejection_code` | const `stock_not_directly_writable` | yes | |
| `attempted_field` | const `current_stock` | yes | |

### `ingredient_price_variance_detected`

Emit when `abs(observed - baseline) / baseline > 0.10` for the same `product_id` and `supplier_id`. Skip when baseline is 0. Baseline is the median `unit_cost` of prior inbound events for that pair.

| Property | Type | Required | Description |
| --- | --- | --- | --- |
| shared inventory fields | | yes | `quantity` is the inbound quantity that tripped the check |
| `supplier_id` | string | yes | |
| `baseline_unit_cost` | number ≥ 0 | yes | |
| `observed_unit_cost` | number ≥ 0 | yes | |
| `variance_ratio` | number ≥ 0 | yes | Absolute relative difference |
| `variance_threshold_ratio` | const `0.10` | yes | |
| `order_id` | integer | yes | The inbound order |

### Identified event properties

`inventory_order_validation_failed`: required `order_kind` (`inbound` or `outbound`), `failure_code` (`insufficient_stock`, `invalid_reason`, `invalid_body`), `http_status` (400 or 422). Optional `location_id`, `product_id`, `quantity` when the body parsed that far. No raw body.

`stock_threshold_edit_rejected`: required `location_id`, `country`, `product_id`, `product_category`, `attempted_threshold` (number ≥ 0), `unit`, `currency`, `rejection_code` const `threshold_not_operator_writable`.

`auth_login_failed`: required `failure_code` const `invalid_credentials`. One code covers a bad password and an unknown address, so the event does not reveal which emails exist. No attempted email.

`auth_login_succeeded`: required `role` (`admin` or `user`). No email.

`auth_session_expired`: required `failure_code` const `token_expired`.

`api_latency_recorded`: required `route` (path template, such as `/inventory/orders/outbound`), `http_method`, `http_status`, `duration_ms` (integer ≥ 0). No query string.

`backoffice_page_viewed`: required `route` (template only).

`backoffice_flow_abandoned`: required `flow_name` (`inbound_delivery`, `outbound_exit`, `login`), `last_step` (string token, not typed text), `route`.

`client_error_uncaught`: required `error_name` (exception name only), `route`. No message and no stack. Messages can contain what the operator typed.

## Phase 3 — Delivery

Stream means the event is available for a decision the same service period. Batch means a daily rollup is enough. Urgency is operational, not a preference for a queue product.

| `event_type` | Delivery | Why this urgency |
| --- | --- | --- |
| `stock_threshold_triggered` | stream | A kitchen can run out during the current service. Felipe cannot wait until tomorrow. |
| `direct_stock_edit_rejected` | stream | A traceability bypass is a control incident the same day. |
| `stock_threshold_edit_rejected` | stream | Same control question, same day. |
| `ingredient_price_variance_detected` | stream | A beef price jump changes what Lucía buys on the next order, not next week’s slide. |
| `inventory_order_validation_failed` | stream | The operator is blocked at the counter now. |
| `auth_login_failed` | stream | A burst of failures is a lockout or an attack today. |
| `client_error_uncaught` | stream | A broken page is lying about counts until someone patches it. |
| `inbound_order_created` | batch (daily) | Price talks and purchase consolidation are weekly. A daily file is enough. |
| `outbound_order_created` | batch (daily) | Reorder suggestions use a consumption rate, not the minute of one ticket. |
| `stock_waste_registered` | batch (daily) | Audit priority is “worst locations this week”, not an interrupt per expired tray. |
| `auth_login_succeeded` | batch (daily) | Session counts explain failure spikes after the day closes. |
| `auth_session_expired` | batch (daily) | Token lifetime is a weekly product decision. |
| `api_latency_recorded` | batch (daily aggregate) | The decision is which route was slow today, not a page per request. |
| `backoffice_page_viewed` | batch (daily) | Black-box screens show up in a daily visit count. |
| `backoffice_flow_abandoned` | batch (daily) | Form changes ship in a release, not mid-service. |

### Throttle

High-frequency events only:

- `api_latency_recorded`: at most one event per `route` + `http_method` per 60 seconds. `duration_ms` is the max in that window. `http_status` is the status of that slowest call.
- `backoffice_page_viewed`: at most one event per `route` per `sessionId` per 30 seconds.
- `client_error_uncaught`: at most one event per `error_name` + `route` per `sessionId` per 60 seconds.

Order, auth, and threshold events are not throttled. Dropping one would hide a purchase, a rejection, or a stock-out.

### Risks and exclusions

Considered and discarded:

- Brasa Points registration and any customer field. The RFI is the inventory system and the backoffice. Customer data is out of scope, and the brief forbids customer data in `properties`.
- `email`, password, reset token, and the typed login address. A failed-login count does not need them. Splitting `invalid_credentials` into “unknown email” and “bad password” would tell an attacker which addresses are real.
- Raw request bodies, validation `input` values, stack traces, and file paths. A previous Brasaland rule already keeps those out of API responses. The same strings must not reappear in telemetry.
- UI language (Spanish/English). The brief says language is not `country`.
- Per-keystroke and click-coordinate events. They do not change a purchasing, waste, or access decision, and they are expensive.
- A successful `stock_edited` event. Stock is never written directly. Emitting a success event would contradict the traceability rule.
- Mapping today’s single reason `waste` onto `expired` by default. That would send Felipe to audit the wrong cause.

Known gap the instrumenter must not paper over: live stock is one chain-wide number, and live waste has no `expired` / `kitchen_error` / `theft_suspected` split. Threshold and waste events wait until location stock and the three reasons exist. Until then, still emit `outbound_order_created` for `consumption`, `inbound_order_created`, validation failures, and `direct_stock_edit_rejected`.

## What the next developer changes

No new server. When instrumentation starts, emit only after the database commit succeeds, except rejections, which emit instead of a commit. Join events from one HTTP call with `requestId`. Validate the body against `event-schemas.json` before send. Reject unknown properties.
