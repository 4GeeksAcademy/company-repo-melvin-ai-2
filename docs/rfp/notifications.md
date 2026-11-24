# RFP ticket notifications

`POST /rfp/tickets` still saves the PDF and opens the ticket at `analyzing`. That save publishes one Server-Sent Event. The backoffice page `/rfp` shows it without a manual reload.

## Event

The event name is `rfp_ticket_created`. The JSON data uses the stored ticket fields from the briefing:

- `ticket_id`
- `status`, which is `analyzing` at registration
- `created_at`

The stored ticket has no separate `rfp_id` column, so the event does not invent one. The response uses `Content-Type: text/event-stream`. An idle connection receives a `: keep-alive` comment every 15 seconds.

`GET /rfp/tickets/stream` uses the same bearer JWT as the rest of the backoffice. A missing token is rejected and receives no frames. The page opens the stream with `fetch` and `ReadableStream`, and it sets `Authorization: Bearer …`. It does not use `EventSource`, because that API cannot set the header.

## Connections

Each open dashboard has its own stream and its own queue. Those queues live in the API process that accepts the upload. One registration is copied to every open queue, so two salespeople both see the ticket, and about fifty open dashboards are fifty streams in that same process. There is no shared replay buffer.

## Recovery

If the stream drops, the page waits 1 second, then 2, 4, 8, 16, and then 30 seconds, and opens the stream again. Before that new stream, it refetches `GET /rfp/tickets` once. A `ticket_id` already on the page is not given a second notice. Events after the refetch are applied one at a time and do not reload the whole list.

While the open ticket is `analyzing` or `drafting`, the page reloads that one ticket so the later status can appear. That follow-up is not the new-ticket notice.

## Why SSE

The server only announces that a ticket arrived. Upload, drafting, and approval stay on their existing POST routes. A WebSocket would be the right tool if a salesperson had to approve or reject on that same channel.

This part does not call a model or an agent.
