# RFP drafts

Part 2 starts from a ticket whose status is `intake_complete`. The graph reads `handoff_json` (`ticket_id`, metadata, and `key_aspects` by department). It does not open the PDF again.

Each briefing department has its own generator: `generate_marketing`, `generate_operaciones`, `generate_procurement`, and `generate_training`. A department that Part 1 did not select does no work. The four department graphs run in the same step, so one department does not wait for another to finish.

## Evaluators

Three evaluators read only the section they are scoring:

- Readability uses `py-readability-metrics`. Flesch-Kincaid needs 100 words, so a shorter section fails.
- Relevance checks that each `key_aspects` line from the handoff appears in the draft.
- Compliance checks briefing section 5: both currencies when a price is present (`dual-currency`, 4,000 COP per USD, the same rate as `src/utils/transformations.ts`), the three brand pillars (`brand-pillars`), setup of at least 10 business days (`setup-sla`), no competitor name (`no-competitors`), and a 30-day offer (`offer-validity`).

A contract above USD 50,000 sets `ceo_approval_required` on the handoff for Part 3. That flag does not fail the draft.

Each evaluator returns its own field. The join step builds one `EvaluationResult`:

- `department_id`
- `readability`: `pass`, `score`, `details`
- `relevance`: `pass`, `missing_aspects`
- `compliance`: `pass`, `rule_ids`, `violations`
- `overall_pass`
- `feedback_for_generator`

The feedback names the failed rule and the change to make. A missing price stays an open question. The generator does not invent a number.

## Loop

A failed section goes back to its own generator with that feedback. The first draft plus two revisions is the limit. If it still fails, the last draft and its evaluation stay on the section, `approval_status` is `needs_human_review`, and the other departments are kept. The ticket status is `needs_human_review` when any section hits that limit. When every section passes, the ticket stays `under_evaluation` and each section is `pending`. Part 3 statuses are not set.

The backoffice page `/rfp` shows the provisional section and the last feedback. Sales polls the same ticket.

## Status

`POST /rfp/tickets/{ticket_id}/draft` returns `202` and sets `drafting`. Evaluators move the ticket to `under_evaluation` while they run. Drafts and `evaluation_results` are columns on `rfp_department_sections`.
