# RFP approval

Part 3 starts from a ticket whose status is `under_evaluation` or `needs_human_review`. It uses the drafts and evaluations already stored on that ticket. It does not open the PDF and it does not run the Part 2 generators again.

## Pause and resume

Each department has its own graph and its own checkpoint thread, `rfp-{ticket_id}:{department}`. The checkpoint is a SQLite file at `data/agent_memory/rfp_approval.sqlite`. Two tickets do not share a thread, and approving one department does not resume another.

`POST /rfp/tickets/{ticket_id}/approval` moves the ticket to `waiting_for_approval` and pauses every ready department. The signer sees that department's draft, whether evaluation passed, the feedback, and the open questions.

`POST /rfp/tickets/{ticket_id}/approval/{department_id}` resumes that thread only. The body is `{"decision": "approve" | "reject" | "request_changes"}`. Any other value is refused. A rejection keeps the section and leaves the final document unwritten. Request changes can return to the same pause twice. The third change is not offered.

## Arbitration

Before the pauses, one `arbitrate` node reads structured state:

- `setup-sla-breach`: a section promises fewer than 10 business days. Felipe Guerrero's rule rewrites it to 10 business days. Camila Ospina is recorded when the breach is outside operaciones.
- `cost-vs-feasibility`: procurement's USD amount is higher than the operaciones amount. Camila Ospina raises the operaciones price to that amount, in USD and COP at 4,000 COP per USD.
- `ceo-threshold`: the budget is at least USD 50,000 and Mariana Restrepo has not approved. The final document stays blocked until she signs. She is not another drafting department.

The loop stops after two rounds even if a breach remains. Every node records the agent, the input, the output, and a timestamp on the ticket.

## Final document

When every department section is approved, and Mariana has approved when the contract requires it, the ticket becomes `done`. The document is stored on the ticket and shown on `/rfp`. It names the client, the approved sections, both currencies when a price was stated, the three brand pillars, a 30-day offer, and a setup time of 10 business days.
