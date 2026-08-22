# Delivery Verification

## Objective
Determine whether one Brasaland change is ready for developer-approved commit by running the same evidence-based delivery check every time.

## Inputs
- `changed_paths`: files included in the proposed delivery.
- `target`: affected app, service, package, or documentation area.
- `acceptance_criteria`: observable conditions from the request.
- `commands`: lint, type-check, test, build, and run commands documented by the target.

## Procedure
1. Read `CONTEXT.md`, every memory-bank file, `AGENTS.md`, and rules under `.agents/rules/` that match `changed_paths`.
2. Inspect `git status` and the complete diff. Flag unrelated edits, generated files, secrets, protected paths without approval, misplaced APIs, or duplicated business logic.
3. Run every relevant command from `commands`. A missing required command is a failure, not a skipped check.
4. For UI changes, start the application and verify the affected routes render the expected visible output and remain keyboard-usable at mobile and desktop widths.
5. Compare the result with each acceptance criterion and update `memory-bank/progress.md` with completed checks and remaining risks.
6. Report pass/fail evidence and request explicit developer approval before committing.

## Acceptance Criteria
The skill passes only when all of these are verifiably true:
- Required context and scoped rules were reviewed.
- Every changed file is in the correct monorepo location.
- No protected path changed without developer approval.
- No API or shared business logic is implemented inside a UI.
- Relevant lint, type-check, tests, and production builds exit successfully.
- Changed UI routes render visible expected output.
- The request’s acceptance criteria are individually satisfied.
- Progress documentation reflects the actual repository state.
- Developer confirmation is obtained before the commit.

If any criterion fails, return `NOT READY` with the failed check and recommended next action. Otherwise return `READY FOR APPROVAL` with the commands and routes verified.
