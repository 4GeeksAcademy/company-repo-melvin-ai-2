# Progress

## Current Milestone
Supplier Directory — TinyDB + FastAPI CRUD and backoffice UI on branch `Supplier_directory`.

## Completed
- Added the business and technical memory bank, root agent workflow, scoped rules, and delivery-verification skill.
- Reorganized agent config to `.agents/rules/` and `.agents/skills/` (including dual-currency and delivery-verification skills).
- Added always-on `.agents/rules/company-context.md` so every milestone uses Brasaland only.
- Rebuilt the complete public website as reusable Next.js components at `uis/website`.
- Added the validated Brasa Points registration route at `/brasa-points`.
- Restored the canonical Milestone 2 models, sample data, and pure utilities under root `src`.
- Built a distinct backoffice operations dashboard that imports and visibly renders those utilities.
- Delivered Company File Analyzer Phase 1 + Phase 2 (CLI, API, `uis/web`).
- Delivered Supplier Directory: CONTEXT in `memory-bank/supplier-directory.md`, TinyDB seeder (15 suppliers), FastAPI `/suppliers` CRUD, backoffice `/suppliers` UI (filters, create, rate, status).

## Verification
- `uis/website`: lint passed; Next.js production build passed.
- `uis/backoffice`: lint passed; Next.js production build passed (includes `/suppliers`).
- Supplier API smoke tests: seed inserts 15; list/filter; 422 on currency/category errors; rate PATCH sets `updated_at`; seeder idempotent.
- Development smoke tests returned HTTP 200 with expected visible content for website `/`, website `/brasa-points`, and backoffice `/`.
- Backoffice calculations are imported from root `src`; no calculation implementation was copied into the UI.

## Next Steps
- Optional polish: auth for internal tools, persistence beyond in-memory last analysis.
- Future milestones may still add Brasa Points persistence, backoffice authentication, inventory forecasting, and People & Talent workflows.

## Documentation
- Updated `docs/ARCHITECTURE_PROPOSAL.md` into a CTO-facing FastAPI backend proposal.
- Company File Analyzer CONTEXT: `memory-bank/company-file-analyzer.md`.
- Supplier Directory CONTEXT: `memory-bank/supplier-directory.md` (root `CONTEXT.md` points there; `scripts/CONTEXT-brasaland.en.md` is a pointer).

## Incident Report Processor (Phase 1)
- Sample CSV: `scripts/incidents-brasaland.csv` (**100-row** grading sample).
- CLI: `scripts/analyze.py` — verified 100/96/4 and average satisfaction **3.46**.

## Incident Report Processor (Phase 2)
- Shared analysis module + FastAPI endpoints under `services/api`.
- UI: `uis/web` Incident analysis page.

## Supplier Directory
- Models + TinyDB at `services/api/app/suppliers/`; idempotent seeder (`python seed.py` / `uv run seed`); auto-seed on empty startup.
- Endpoints: `POST/GET /suppliers`, `GET /suppliers/{id}`, `PATCH .../rate`, `PATCH .../status`, `DELETE /suppliers/{id}`.
- Backoffice: `uis/backoffice` port **3101**, page `/suppliers` (table, country/category filters, create form, inline rate + status).
