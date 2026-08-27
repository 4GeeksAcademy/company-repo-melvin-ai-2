# Progress

## Current Milestone
Brasaland Identity — planning complete; implementation not started. Follow [`docs/masterplan.md`](../docs/masterplan.md) on branch `feature/brasaland-auth`, Sprint 1 first.

## Completed
- Added the business and technical memory bank, root agent workflow, scoped rules, and delivery-verification skill.
- Reorganized agent config to `.agents/rules/` and `.agents/skills/` (including dual-currency and delivery-verification skills).
- Added always-on `.agents/rules/company-context.md` so every milestone uses Brasaland only.
- Rebuilt the complete public website as reusable Next.js components at `uis/website`.
- Added the validated Brasa Points registration route at `/brasa-points`.
- Restored the canonical Milestone 2 models, sample data, and pure utilities under root `src`.
- Built a distinct backoffice operations dashboard that imports and visibly renders those utilities.
- Delivered Company File Analyzer Phase 1 + Phase 2 (CLI, API, `uis/web`).
- Delivered Supplier Directory: CONTEXT in `memory-bank/supplier-directory.md`, TinyDB seeder (15 suppliers), FastAPI `/suppliers` CRUD, `uis/backoffice/app/suppliers` UI (filters, create, rate, status).
- Wrote Brasaland Identity master plan at `docs/masterplan.md` (one branch, three sprint checklists; no auth implementation yet).

## Verification
- `uis/website`: lint passed; Next.js production build passed.
- `uis/backoffice`: lint passed; Next.js production build passed (includes `/suppliers`).
- Supplier API smoke tests: seed inserts 15; list/filter; 422 on currency/category errors; rate PATCH sets `updated_at`; seeder idempotent.
- Development smoke tests returned HTTP 200 with expected visible content for website `/`, website `/brasa-points`, and backoffice `/`.
- Backoffice calculations are imported from root `src`; no calculation implementation was copied into the UI.
- Brasaland Identity planning pass: documentation only (`docs/masterplan.md`, `memory-bank/progress.md`). No API or UI auth code. No protected paths changed.

## Next Steps
- Implement Brasaland Identity **Sprint 1 (AUTH-01)** from [`docs/masterplan.md`](../docs/masterplan.md): TinyDB User + Profile, JWT, protect suppliers and incident routes, seed Lucía Fernández as admin. Do not start Sprint 2 until Sprint 1’s checklist passes.
- Sprint 2: `@repo/auth` + thin routes in backoffice, incident web, and talent tracker (Playground candidate API unchanged).
- Sprint 3: Resend password reset and change-password.
- Optional later: persistence beyond in-memory last incident analysis; Brasa Points persistence; inventory forecasting.

## Documentation
- Updated `docs/ARCHITECTURE_PROPOSAL.md` into a CTO-facing FastAPI backend proposal.
- Company File Analyzer CONTEXT: `memory-bank/company-file-analyzer.md`.
- Supplier Directory CONTEXT: `memory-bank/supplier-directory.md` (root `CONTEXT.md` points there; `scripts/CONTEXT-brasaland.en.md` is a pointer).
- Brasaland Identity master plan: [`docs/masterplan.md`](../docs/masterplan.md) (AUTH-01 / AUTH-02 / AUTH-03 combined; no auth code in this pass).

## Incident Report Processor (Phase 1)
- Sample CSV: `scripts/incidents-brasaland.csv` (**100-row** grading sample).
- CLI: `scripts/analyze.py` — verified 100/96/4 and average satisfaction **3.46**.

## Incident Report Processor (Phase 2)
- Shared analysis module + FastAPI endpoints under `services/api`.
- UI: `uis/web` Incident analysis page.

## Supplier Directory
- Submission layout: `services/api/{main,models,database,seed}.py` + `routes/suppliers.py`; UI at `uis/backoffice/app/suppliers/`.
- Idempotent seeder (`uv run seed` / `python seed.py`); auto-seed on empty startup; TinyDB at `data/suppliers.json`.
- Endpoints: `POST/GET /suppliers`, `GET /suppliers/{id}`, `PATCH .../rate`, `PATCH .../status`, `DELETE /suppliers/{id}`.
- Backoffice UI: port **3101**, `/suppliers` (table with CONTEXT fields, filters, create, rate, status).
