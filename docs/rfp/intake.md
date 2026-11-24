# RFP intake

Camila Ospina uploads a PDF in the backoffice. The existing API stores it under `data/raw/rfp/` and opens a ticket with status `analyzing`. The intake graph in `data/pipelines/rfp_intake/` then converts the PDF to Markdown, scores readability, and either discards the ticket or writes one section per department. The support-agent graph is not involved.

The brief is `docs/rfp/brasaland-BRIEFING.md`. Departments are `marketing` (Camila Ospina), `operaciones` (Felipe Guerrero), `procurement` (Lucía Fernández), and `training` (Jake Morrison).

## Conversion

MarkItDown is the converter named in the lesson. The current release depends on onnxruntime, and that package has no wheel for Intel macOS, so this step uses pdfminer.six and wraps the extracted text as Markdown. If MarkItDown imports, it is used first. Agents read the Markdown only.

Readability is Flesch-Kincaid and Gunning Fog from `py-readability-metrics`. The scores estimate processing cost. They are not a writing grade.

## Decisions

- A department named in the PDF that is not in the briefing, such as legal, is recorded on the ticket and does not get a worker.
- Each worker sees the sentences that concern that department, plus the shared metadata. A missing budget or volume is an open question. The worker does not invent a number.
- A document is an RFP when it names a service (catering, concession, or co-branding) and a scope or a deadline. A franchise inquiry with none of those is `discarded`. That stop applies only to that ticket. A false negative stays visible as a discarded ticket.
- If two departments quote different amounts, the synthesizer keeps both and says they conflict.
- The upload returns as soon as the PDF is stored. `BackgroundTasks` runs the graph in the same API process. The page hears about that registration on `GET /rfp/tickets/stream`, described in [`notifications.md`](./notifications.md). A crash leaves the ticket at `analyzing` and stores `error_detail`. Part 1 does not add another status.
- Part 2 reads `handoff_json` on the ticket. It carries `ticket_id`, the metadata, and `key_aspects` by department. The draft graph is described in `docs/rfp/draft.md`.

## Samples

`docs/rfp/rfp-requests/brasaland/brasaland-request-1.pdf` is the formal Sunset Bay Resorts RFP and is accepted for all four departments. Request 2 is the informal Andes Tech catering letter, written in Spanish, and skips training. Request 3 is a franchise inquiry, also in Spanish, and is discarded. All three files are the official sample PDFs.
