"""OAuth on the MCP server, and the same routing the agent already had."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
for path in (str(ROOT), str(API)):
    if path not in sys.path:
        sys.path.insert(0, path)

from mcps.brasaland_tools import operations  # noqa: E402
from mcps.brasaland_tools.server import build_app  # noqa: E402

AUDIENCE = "brasaland-mcp"
SCOPES = "incidents:read incidents:write inventory:read"


def _jwks_server():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    public.update({"kid": "test", "use": "sig", "alg": "RS256"})
    body = json.dumps({"keys": [public]}).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            raw = body if self.path == "/jwks" else b""
            self.send_response(200 if raw else 404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return key, server


def _token(key, issuer: str, scope: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "iss": issuer,
            "aud": AUDIENCE,
            "sub": "support-agent",
            "client_id": "brasaland-support",
            "scope": scope,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        key,
        algorithm="RS256",
        headers={"kid": "test"},
    )


def _rpc(response) -> dict:
    for line in response.text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[len("data: ") :])
    return response.json()


def _post(client: TestClient, payload: dict, token: str | None, session: str | None):
    headers = {"Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if session:
        headers["mcp-session-id"] = session
    response = client.post("/mcp", json=payload, headers=headers)
    session_id = response.headers.get("mcp-session-id") or session
    return response, session_id


def _ready(client: TestClient, token: str) -> str | None:
    response, session = _post(
        client,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "brasaland-test", "version": "0"},
            },
        },
        token,
        None,
    )
    assert response.status_code == 200, response.text
    noted, session = _post(
        client,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        token,
        session,
    )
    assert noted.status_code in {200, 202}
    return session


def _call(client, token, session, name, arguments, request_id=3):
    response, session = _post(
        client,
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        token,
        session,
    )
    return response, session


def test_missing_token_cannot_list_tools(tmp_path, monkeypatch):
    key, jwks = _jwks_server()
    port = jwks.server_address[1]
    issuer = f"http://127.0.0.1:{port}"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mcp.db'}")
    monkeypatch.setenv("MCP_ISSUER", issuer)
    monkeypatch.setenv("MCP_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("MCP_JWKS_URI", f"{issuer}/jwks")
    from app.inventory.db import reset_engine

    reset_engine()
    try:
        with TestClient(build_app()) as client:
            response, _session = _post(
                client,
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                None,
                None,
            )
            assert response.status_code == 401
            body = response.json()
            assert "bearer" in body["error_description"].lower()
            assert "read-only" not in body["error_description"].lower()
            metadata = client.get("/.well-known/oauth-protected-resource")
            assert metadata.status_code == 200
            assert "incidents:read" in metadata.json()["scopes_supported"]
            assert client.get("/.well-known/oauth-authorization-server").status_code == 200
    finally:
        jwks.shutdown()
        key.private_numbers()


def test_lifecycle_illegal_status_and_read_only_inventory(tmp_path, monkeypatch, caplog):
    key, jwks = _jwks_server()
    port = jwks.server_address[1]
    issuer = f"http://127.0.0.1:{port}"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mcp.db'}")
    monkeypatch.setenv("MCP_ISSUER", issuer)
    monkeypatch.setenv("MCP_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("MCP_JWKS_URI", f"{issuer}/jwks")
    from app.inventory.db import reset_engine

    reset_engine()
    token = _token(key, issuer, SCOPES)
    reader = _token(key, issuer, "inventory:read")
    caplog.set_level("INFO", logger="brasaland.mcp")
    patches: list[tuple[str, dict]] = []
    send_patch = operations._send_status_patch

    def _record_patch(path: str, payload: dict):
        patches.append((path, payload))
        return send_patch(path, payload)

    monkeypatch.setattr(operations, "_send_status_patch", _record_patch)
    try:
        with TestClient(build_app()) as client:
            session = _ready(client, token)
            listed, session = _post(
                client,
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                token,
                session,
            )
            assert listed.status_code == 200
            tools = {tool["name"]: tool for tool in _rpc(listed)["result"]["tools"]}
            assert {
                "create_incident",
                "get_incident",
                "list_incidents",
                "change_status",
                "read_inventory",
                "write_inventory",
            } <= set(tools)
            create_fields = tools["create_incident"]["inputSchema"]["properties"]
            assert {"title", "description", "category", "status", "origin", "branch"} <= set(
                create_fields
            )
            assert "current_stock" in json.dumps(tools["read_inventory"]["outputSchema"])
            assert "status" in json.dumps(tools["change_status"]["inputSchema"])

            created, session = _call(
                client,
                token,
                session,
                "create_incident",
                {
                    "title": "Fryer down",
                    "description": "The fryer stopped heating during service.",
                    "category": "equipment_failure",
                    "status": "open",
                    "origin": "branch",
                    "branch": "medellin_centro",
                },
                4,
            )
            assert created.status_code == 200, created.text
            ticket = json.loads(_rpc(created)["result"]["content"][0]["text"])
            ticket_id = ticket["tickets"][0]["id"]
            assert ticket["tickets"][0]["status"] == "open"

            moved, session = _call(
                client,
                token,
                session,
                "change_status",
                {"ticket_id": ticket_id, "status": "in_progress"},
                5,
            )
            assert moved.status_code == 200, moved.text
            assert "in_progress" in moved.text
            assert patches[0] == (
                f"/api/incidents/{ticket_id}/status",
                {"status": "in_progress"},
            )

            resolved, session = _call(
                client,
                token,
                session,
                "change_status",
                {"ticket_id": ticket_id, "status": "resolved"},
                6,
            )
            assert resolved.status_code == 200, resolved.text

            illegal, _session = _call(
                client,
                token,
                session,
                "change_status",
                {"ticket_id": ticket_id, "status": "open"},
                7,
            )
            assert illegal.status_code == 400
            assert "not allowed" in illegal.text

            denied, _session = _call(
                client,
                token,
                session,
                "write_inventory",
                {"ingredient_id": 1, "quantity": 4},
                8,
            )
            assert denied.status_code == 403
            assert "read-only" in denied.text
            assert "not allowed" not in denied.text

            wrong_scope, _session = _call(
                client,
                reader,
                None,
                "create_incident",
                {
                    "title": "No",
                    "description": "This token cannot open a ticket.",
                    "category": "other",
                    "status": "open",
                    "origin": "internal",
                    "branch": "central",
                },
                9,
            )
            assert wrong_scope.status_code == 403
            assert "incidents:write" in wrong_scope.text
            assert "read-only" not in wrong_scope.text
    finally:
        jwks.shutdown()

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "client=brasaland-support tool=create_incident result=ok" in logged
    assert "client=brasaland-support tool=write_inventory result=" in logged


def test_bad_field_is_400(tmp_path, monkeypatch):
    key, jwks = _jwks_server()
    port = jwks.server_address[1]
    issuer = f"http://127.0.0.1:{port}"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mcp.db'}")
    monkeypatch.setenv("MCP_ISSUER", issuer)
    monkeypatch.setenv("MCP_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("MCP_JWKS_URI", f"{issuer}/jwks")
    from app.inventory.db import reset_engine

    reset_engine()
    token = _token(key, issuer, SCOPES)
    try:
        with TestClient(build_app()) as client:
            session = _ready(client, token)
            response, _session = _call(
                client,
                token,
                session,
                "create_incident",
                {
                    "title": " ",
                    "description": "A title is required before this can be saved.",
                    "category": "other",
                    "status": "open",
                    "origin": "internal",
                    "branch": "central",
                },
            )
            assert response.status_code == 400
            assert "Enter a short title." in response.text
    finally:
        jwks.shutdown()
