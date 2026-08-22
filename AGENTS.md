# Agent Operating Guide

## Session Startup
Before changing code, every agent must read:
1. `CONTEXT.md`
2. `memory-bank/projectbrief.md`
3. `memory-bank/techContext.md`
4. `memory-bank/progress.md`
5. Every applicable rule in `.agents/rules/`

Then inspect the working tree, preserve existing user changes, and state which acceptance criteria the work will satisfy.

## Development Rules
- Put UI applications in `uis`, APIs in `services`, reusable libraries in `packages`, and canonical Milestone 2 logic in `src`.
- Use Brasaland terminology and real project constraints; do not introduce generic placeholder products.
- Prefer small typed components and pure functions. Do not duplicate shared logic in application code.
- Keep public experiences mobile-first and accessible. Keep the backoffice layout separate from the public site.
- Add or update documentation whenever an application, service, package, rule, or skill changes.

## Mandatory Pre-Commit Delivery Workflow
Agents must complete these ordered steps before every commit:
1. **Review scope:** reread the applicable memory and `.agents/rules` files, then inspect `git status` and the complete diff.
2. **Protect boundaries:** confirm changed files are in the correct monorepo location, no business logic was copied, and no protected path changed without approval.
3. **Verify behavior:** run the relevant lint, type-check, test, and production-build commands; start affected applications when visible behavior changed.
4. **Close delivery:** compare the result with the request and acceptance criteria, update `memory-bank/progress.md`, report verification results, and obtain explicit developer confirmation to commit.

No agent may commit—or describe work as delivery-ready—when any required step fails.

## Protected Paths
Do not modify these without explicit developer confirmation:
- `CONTEXT.md`
- `memory-bank/projectbrief.md`
- `memory-bank/techContext.md`
- `AGENTS.md`
- `.agents/`
- `src/`
- Dependency lockfiles and root workspace configuration

`memory-bank/progress.md` is intentionally writable during the delivery workflow. Generated files, credentials, and unrelated user changes must never be committed.
