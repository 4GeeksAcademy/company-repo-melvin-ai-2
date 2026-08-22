# Dual-Currency Operations Metrics

## Objective
Display Brasaland operations metrics so every money value is correctly labeled in USD or COP, uses the shared `Price` model, and never invents exchange rates or formats outside the business rules.

## Inputs
- `metric_name`: what is being shown (revenue, average ticket, waste cost, margin, location score)
- `currency`: `USD` or `COP`
- `value`: number produced by an imported calculation in root `src/`
- `source_fn`: name of the root utility that produced the value (for example `calculateAverageTicket`)

## Expected output
- UI copy that includes the currency code or a locale currency string for that code
- Margin and location scores shown as percentages or 0–100 scores, never as currency
- Confirmation that the value came from root `src` and was not recalculated inside a UI component

## Procedure
1. Identify every money, margin, and score metric in the target view.
2. Trace each value to its `source_fn` under `src/utils/` (or equivalent canonical module).
3. Reject any UI that hardcodes `1 USD = 4000 COP` or reimplements a calculation already in `src`.
4. Ensure money metrics use explicit `USD`/`COP` labeling or matching `Intl` currency formatting.
5. Ensure margin uses `%` and location performance uses a 0–100 score.
6. Report pass/fail against the acceptance criteria with the metrics checked.

## Acceptance criteria
- Every money metric shows an explicit currency (`USD` or `COP`) or a locale format for that code.
- Margin uses `%`; location performance uses a 0–100 score — neither is formatted as money.
- No hardcoded USD↔COP conversion appears in UI code; conversion stays in `src/utils/transformations.ts`.
- The component imports calculations; it does not reimplement `calculateAverageTicket`, `calculateWasteCost`, `calculateLocationMargin`, or similar.
- Sample or live numbers match the return value of the named `source_fn` for the same inputs.

If any criterion fails, return `NOT READY` with the failed metric and fix. Otherwise return `READY` with the metrics and source functions verified.
