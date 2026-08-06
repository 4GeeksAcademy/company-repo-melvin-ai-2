# Progress

## Current Milestone
Company File Analyzer / Incident Report Processor — Phase 1 CLI and Phase 2 API + `uis/web` delivered.

## Completed
- Added the business and technical memory bank, root agent workflow, scoped rules, and delivery-verification skill.
- Reorganized agent config to `.agents/rules/` and `.agents/skills/` (including dual-currency and delivery-verification skills).
- Added always-on `.agents/rules/company-context.md` so every milestone uses Brasaland only.
- Rebuilt the complete public website as reusable Next.js components at `uis/website`.
- Added the validated Brasa Points registration route at `/brasa-points`.
- Restored the canonical Milestone 2 models, sample data, and pure utilities under root `src`.
- Built a distinct backoffice operations dashboard that imports and visibly renders those utilities.

## Verification
- `uis/website`: lint passed; Next.js production build passed.
- `uis/backoffice`: lint passed; Next.js production build passed.
- Development smoke tests returned HTTP 200 with expected visible content for website `/`, website `/brasa-points`, and backoffice `/`.
- Backoffice calculations are imported from root `src`; no calculation implementation was copied into the UI.
- Repository diff check and editor diagnostics passed.

## Next Steps
- Optional polish: auth for internal tools, persistence beyond in-memory last analysis.
- Future milestones may still add Brasa Points persistence, backoffice authentication, inventory forecasting, and People & Talent workflows.

## Documentation
- Updated `docs/ARCHITECTURE_PROPOSAL.md` into a CTO-facing FastAPI backend proposal: layered domain architecture, `services/api` module layout, operations-first routers, FE/BE separation (monorepo, env, CORS), Milestone 2 TS→Python porting strategy, and risks — with no database choice and auth deferred for v1.
- Added `docs/ARCHITECTURE_PROPOSAL_READABLE.md` (plain-language summary) and `docs/ARCHITECTURE_PROPOSAL.pdf` (printable export of that summary).
- Moved Company File Analyzer assignment context to `memory-bank/company-file-analyzer.md` (schema, invalidation rules, **100-row** expected metrics); root `CONTEXT.md` points there for this assignment.

## Incident Report Processor (Phase 1)
- Moved sample data to `data/incidents-brasaland.csv` (**100-row** grading sample).
- Added `scripts/analyze.py` using rules documented in `memory-bank/company-file-analyzer.md` (aligned with `.agents/rules/incident-report-processor/context.md`).
- Verified against expected values: 100 total, 96 valid, 4 invalid; category/status breakdowns and average satisfaction **3.46** match the assignment context.

## Incident Report Processor (Phase 2)
- Shared analysis module: `services/api/app/incidents/analysis.py` (used by CLI + API).
- FastAPI: `POST /api/incidents/analyze`, `GET /api/incidents/results/export` under `services/api`.
- Next.js app `uis/web` with Incident analysis page (upload, summary, invalid breakdown, CSV download).
- Verification: API TestClient against `data/incidents-brasaland.csv` returned CONTEXT metrics (100/96/4, avg 3.46); `uis/web` production build passed.
