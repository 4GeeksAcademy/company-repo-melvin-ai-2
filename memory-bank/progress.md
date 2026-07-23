# Progress

## Current Milestone
Establish the Brasaland agent infrastructure and deliver the first runnable public and internal Next.js applications.

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
Future milestones may add a centralized API under `services`, persistence for Brasa Points, authentication for the backoffice, inventory forecasting, and People & Talent workflows.
