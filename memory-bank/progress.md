# Progress

## Current Milestone
Company File Analyzer / Incident Report Processor — Phase 1 validation script, then API + UI integration.

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
- Phase 2: expose the same incident analysis via a backend API and web UI (upload, on-screen summary, CSV download).
- Future milestones may still add a centralized API under `services`, persistence for Brasa Points, authentication for the backoffice, inventory forecasting, and People & Talent workflows.

## Documentation
- Updated `docs/ARCHITECTURE_PROPOSAL.md` into a CTO-facing FastAPI backend proposal: layered domain architecture, `services/api` module layout, operations-first routers, FE/BE separation (monorepo, env, CORS), Milestone 2 TS→Python porting strategy, and risks — with no database choice and auth deferred for v1.
- Added `docs/ARCHITECTURE_PROPOSAL_READABLE.md` (plain-language summary) and `docs/ARCHITECTURE_PROPOSAL.pdf` (printable export of that summary).

## Incident Report Processor (Phase 1)
- Moved sample data to `data/incidents-brasaland.csv`.
- Added `scripts/analyze.py` using rules from `.agents/rules/incident-report-processor/context.md`.
- Verified against expected values: 100 total, 96 valid, 4 invalid; category/status breakdowns and average satisfaction **3.46** match CONTEXT.
