# Support-agent memory

The support agent is still the same graph. It reads the manuals through retrieval and the live ticket and stock tools through the MCP server. Memory is one extra step on that graph. It is not a second agent.

## What kind of memory

This store is episodic and key-value. A location manager approves a short operational correction, and a later question can read that correction back. The file is `data/agent_memory/brasaland_agent_memory.sqlite`.

A vector collection was ruled out. Semantic search over the manuals already exists, and the collection name is `brasaland_knowledge`. Writing approved chat into that collection would change retrieval scores and the Recall@3 check. A knowledge graph was ruled out. These corrections are not a hierarchy of dependencies. They are a short list of approved sentences.

`read_memory` and `write_memory` are the only way in. The graph does not keep memory by appending the transcript to the system prompt.

## What may be remembered

A proposal is created when the user states a correction, including `remember that`, `remember this`, `from now on`, `correct the record:`, or a sentence that starts with `actually`. The support agent's generation call asks for that JSON in the same request. The manuals endpoint does not. The same model call returns the spoken `answer` and a `memory_proposal` field. The agent then asks, in that same answer, whether to keep it. Nothing is written at that step.

These three do not propose:

- `How many points do I need for Gold tier?`
- `What is the status of ticket 12?`
- `Do we have beef?`

These three do propose:

- `Remember that Medellín Centro files the waste report in kilograms.`
- `From now on, tell Felipe the fryer ticket is in progress.`
- `Correct the record: supplier orders for Orlando are placed on Monday.`

## What must never be stored

`docs/rag/brasaland-BRIEFING.en.md` is the company briefing used here.

- Official numbers stay in the manuals. An answer must not invent a percentage, an amount, or a points threshold, so those figures are refused as memory.
- Allergen answers cannot be stored as zero risk. The menu allergen guide is the wording.
- Dollar and peso amounts are not converted into a new figure.
- Passwords, tokens, secrets, email addresses, and phone numbers are not memory. Customer contact data stays out of the operational record.

A forbidden sentence is refused and the refusal is logged. It is refused again if the user says to approve it. That is the control against a false correction. Approval is never inferred from the word yes inside a new question. The next message has to be a decision: approve, reject, or `edit: ...`. If that message changes the subject, the pending proposal is logged as rejected and is not stored. Only one proposal is open at a time.

## Consolidation

The same fact is stored once. The newest copy replaces the older one. After that, only the newest 20 approved facts remain. Older rows are deleted. A pending proposal that receives no decision is rejected. A blank follow-up rejects it immediately. A proposal that is still open after 15 minutes is rejected the next time the agent runs, unless that message is an explicit approve, reject, or edit. Silence does not write.

## Evidence cycles

Both cycles are run by `tests/pipelines/test_agent_memory.py`.

Approved. The user says `Remember that Medellín Centro files the waste report in kilograms.` The agent asks to remember it and does not write. The user says `approve`. The audit row records the proposal, the approval, the original message, and the time. A later question, `How should Medellín Centro file the waste report?`, answers with that stored sentence.

Rejected. The user says `Remember that Orlando places supplier orders on Monday.` The user says `no`. The audit row records the rejection. The store does not contain the Monday sentence, and a later question about Orlando does not answer with it.

## Why this is not a multi-agent system

The same model call still writes the answer the user sees. The proposal is a field on that turn, decided by an explicit rule, not by a second agent. The following message is classified against the one pending proposal and then the original graph continues.
