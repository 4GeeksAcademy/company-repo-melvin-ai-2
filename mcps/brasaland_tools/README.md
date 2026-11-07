# Brasaland tools MCP server

Streamable HTTP server for the support agent. It calls the existing incident service and the inventory tables. It does not replace those services.

Auth is [MCP Auth](https://pypi.org/project/mcpauth/). Every MCP call needs a bearer JWT. The server checks the issuer, the audience, and the signature against `MCP_JWKS_URI`. FastMCP's built-in auth helper is not used.

Scopes:

- `incidents:read` — `get_incident`, `list_incidents`
- `incidents:write` — `create_incident`, `change_status`
- `inventory:read` — `read_inventory`

`write_inventory` accepts a write and rejects it. No scope can change stock. A missing or invalid token is HTTP 401. A valid token with the wrong scope is HTTP 403. A bad field or an illegal status change is HTTP 400. An inventory write is HTTP 403 with the read-only message. Those are different codes and different messages.

`change_status` sends `PATCH /api/incidents/{id}/status`. It does not update the whole incident. The lifecycle is `open` to `in_progress` or `discarded`, and `in_progress` to `resolved` or `discarded`. With no `BRASALAND_API_URL`, that PATCH goes to the Incidents Manager route in this process and uses the same database. Set `BRASALAND_API_URL` and `BRASALAND_API_TOKEN` to send it to a running API instead.

Each tool call writes one log line: client id from the token, tool name, and result.

## Start

From the repo root, with `MCP_ISSUER`, `MCP_AUDIENCE`, and `MCP_JWKS_URI` set:

```bash
uv run python -m mcps.brasaland_tools
```

The server listens on port **8765**. The MCP path is `/mcp`.

Protected resource metadata is `GET /.well-known/oauth-protected-resource`. Authorization server metadata is `GET /.well-known/oauth-authorization-server`.

## Local token

When you do not have a paid identity provider, start a local JWKS and print a token:

```bash
uv run python -m mcps.brasaland_tools.dev_auth
```

That process listens on port **8766**. Copy the `export` lines into the shell that starts the MCP server. Leave the JWKS process running.

## MCP Playground

Playground has to use the public Codespaces URL for port 8765, not `localhost`.

1. Run the server in Codespaces.
2. Forward port 8765 and make the forward public.
3. Paste `https://<codespace>-8765.app.github.dev/mcp` into MCP Playground.
4. Send the bearer token from your identity provider, or from `dev_auth`.
5. Run one flow for `create_incident`, `get_incident`, `list_incidents`, `change_status`, and `read_inventory`.
6. Call `write_inventory`. It must fail with the read-only rejection.

That click-through cannot be done from the laptop that only has `localhost`.
