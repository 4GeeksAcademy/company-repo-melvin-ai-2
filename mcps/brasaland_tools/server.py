"""Streamable HTTP MCP server. Auth is MCP Auth, not FastMCP's built-in helper."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Callable

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcpauth import MCPAuth
from mcpauth.config import AuthServerConfig, AuthServerType, AuthorizationServerMetadata
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from mcps.brasaland_tools import AUDIENCE, PORT, SCOPES
from mcps.brasaland_tools.operations import (
    ToolFailure,
    allowed_filter,
    change_ticket_status,
    create_ticket,
    open_session,
    read_stock,
    read_ticket,
)

LOGGER = logging.getLogger("brasaland.mcp")
READ_ONLY = "Inventory is read-only. No scope can change stock."
TICKET_OUTPUT = {
    "type": "object",
    "properties": {
        "found": {"type": "boolean"},
        "tickets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "category": {"type": "string"},
                    "origin": {"type": "string"},
                    "branch": {"type": "string"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                },
                "required": [
                    "id",
                    "title",
                    "status",
                    "category",
                    "origin",
                    "branch",
                    "created_at",
                    "updated_at",
                ],
            },
        },
    },
    "required": ["found", "tickets"],
}
INVENTORY_OUTPUT = {
    "type": "object",
    "properties": {
        "found": {"type": "boolean"},
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "sku": {"type": "string"},
                    "unit": {"type": "string"},
                    "current_stock": {"type": "number"},
                },
                "required": ["id", "name", "sku", "unit", "current_stock"],
            },
        },
    },
    "required": ["found", "products"],
}


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing {name}. Set MCP_ISSUER, MCP_AUDIENCE, and MCP_JWKS_URI "
            "before starting the Brasaland MCP server."
        )
    return value


def build_auth() -> MCPAuth:
    issuer = _env("MCP_ISSUER")
    metadata = AuthorizationServerMetadata(
        issuer=issuer,
        authorization_endpoint=issuer.rstrip("/") + "/authorize",
        token_endpoint=issuer.rstrip("/") + "/token",
        jwks_uri=_env("MCP_JWKS_URI"),
        response_types_supported=["code"],
        grant_types_supported=["authorization_code"],
        code_challenge_methods_supported=["S256"],
        scope_supported=list(SCOPES),
    )
    return MCPAuth(
        server=AuthServerConfig(metadata=metadata, type=AuthServerType.OAUTH)
    )


def protected_resource_document() -> dict:
    resource = os.environ.get("MCP_RESOURCE_URL", f"http://127.0.0.1:{PORT}").rstrip("/")
    return {
        "resource": resource,
        "authorization_servers": [_env("MCP_ISSUER")],
        "scopes_supported": list(SCOPES),
        "bearer_methods_supported": ["header"],
    }


def _summary(result: dict) -> str:
    if "tickets" in result:
        tickets = result.get("tickets") or []
        ident = tickets[0]["id"] if tickets else "none"
        return f"ok tickets={len(tickets)} id={ident}"
    products = result.get("products") or []
    return f"ok products={len(products)}"


def _invoke(auth: MCPAuth, name: str, scope: str, action: Callable[[], dict]) -> dict:
    info = auth.auth_info
    client = "unknown"
    if info is not None:
        client = info.client_id or info.subject or "unknown"
    if info is None or scope not in (info.scopes or []):
        detail = f"HTTP 403: This token does not include the {scope} scope."
        LOGGER.info("client=%s tool=%s result=%s", client, name, detail)
        raise ToolError(detail)
    try:
        result = action()
    except ToolFailure as exc:
        detail = f"HTTP {exc.status}: {exc.detail}"
        LOGGER.info("client=%s tool=%s result=%s", client, name, detail)
        raise ToolError(detail) from exc
    LOGGER.info("client=%s tool=%s result=%s", client, name, _summary(result))
    return result


def build_mcp(auth: MCPAuth) -> FastMCP:
    mcp = FastMCP("Brasaland tools")

    @mcp.tool(
        name="create_incident",
        description="Open a Brasaland incident. Requires the incidents:write scope.",
        output_schema=TICKET_OUTPUT,
        run_in_thread=False,
    )
    def create_incident(
        title: str,
        description: str,
        category: str,
        status: str,
        origin: str,
        branch: str,
    ) -> dict:
        def action() -> dict:
            with open_session() as session:
                return create_ticket(
                    session,
                    {
                        "title": title,
                        "description": description,
                        "category": category,
                        "status": status,
                        "origin": origin,
                        "branch": branch,
                    },
                )

        return _invoke(auth, "create_incident", "incidents:write", action)

    @mcp.tool(
        name="get_incident",
        description="Read one Brasaland incident by id. Requires the incidents:read scope.",
        output_schema=TICKET_OUTPUT,
        run_in_thread=False,
    )
    def get_incident(ticket_id: int) -> dict:
        def action() -> dict:
            with open_session() as session:
                return read_ticket(session, {"ticket_id": ticket_id})

        return _invoke(auth, "get_incident", "incidents:read", action)

    @mcp.tool(
        name="list_incidents",
        description=(
            "List Brasaland incidents. Filters use status, category, origin, and branch. "
            "Requires the incidents:read scope."
        ),
        output_schema=TICKET_OUTPUT,
        run_in_thread=False,
    )
    def list_incidents(
        status: str | None = None,
        category: str | None = None,
        origin: str | None = None,
        branch: str | None = None,
    ) -> dict:
        def action() -> dict:
            query = {
                "status": allowed_filter("status", status),
                "category": allowed_filter("category", category),
                "origin": allowed_filter("origin", origin),
                "branch": allowed_filter("branch", branch),
            }
            with open_session() as session:
                return read_ticket(session, query)

        return _invoke(auth, "list_incidents", "incidents:read", action)

    @mcp.tool(
        name="change_status",
        description=(
            "Move an incident through the Brasaland lifecycle. "
            "open can become in_progress or discarded. "
            "in_progress can become resolved or discarded. "
            "Requires the incidents:write scope."
        ),
        output_schema=TICKET_OUTPUT,
        run_in_thread=False,
    )
    def change_status(ticket_id: int, status: str) -> dict:
        def action() -> dict:
            with open_session() as session:
                return change_ticket_status(session, ticket_id, status)

        return _invoke(auth, "change_status", "incidents:write", action)

    @mcp.tool(
        name="read_inventory",
        description=(
            "Read current_stock for a Brasaland ingredient. Stock is entries minus exits. "
            "Requires the inventory:read scope."
        ),
        output_schema=INVENTORY_OUTPUT,
        run_in_thread=False,
    )
    def read_inventory(product: str) -> dict:
        def action() -> dict:
            with open_session() as session:
                return read_stock(session, product)

        return _invoke(auth, "read_inventory", "inventory:read", action)

    @mcp.tool(
        name="write_inventory",
        description=(
            "Request a stock change. No scope grants an inventory write. "
            "The call is rejected because inventory is read-only."
        ),
        output_schema=INVENTORY_OUTPUT,
        run_in_thread=False,
    )
    def write_inventory(ingredient_id: int, quantity: float) -> dict:
        def action() -> dict:
            if ingredient_id <= 0:
                raise ToolFailure(400, "Choose an ingredient.")
            raise ToolFailure(403, READ_ONLY)

        return _invoke(auth, "write_inventory", "inventory:read", action)

    return mcp


class RewriteToolStatus(BaseHTTPMiddleware):
    """Turn a coded tool error into its own HTTP status. Auth codes stay as they are."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        chunks: list[bytes] = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        body = b"".join(chunks)
        status = response.status_code
        if b"isError" in body:
            match = re.search(br"HTTP (\d{3}):", body)
            if match:
                status = int(match.group(1))
        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in {"content-length"}
        }
        return Response(
            content=body,
            status_code=status,
            headers=headers,
            media_type=response.media_type,
        )


def build_app():
    auth = build_auth()
    mcp = build_mcp(auth)
    mcp_http = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        stateless_http=True,
        host_origin_protection=False,
    )
    audience = os.environ.get("MCP_AUDIENCE", AUDIENCE).strip() or AUDIENCE
    bearer = auth.bearer_auth_middleware("jwt", audience=audience)

    class Gate(bearer):
        async def dispatch(self, request: Request, call_next) -> Response:
            if request.url.path.startswith("/.well-known/"):
                return await call_next(request)
            return await super().dispatch(request, call_next)

    async def protected(_request: Request) -> Response:
        return JSONResponse(protected_resource_document())

    mcp_http.routes.insert(0, auth.metadata_route())
    mcp_http.routes.insert(
        0,
        Route(
            "/.well-known/oauth-protected-resource",
            protected,
            methods=["GET", "OPTIONS"],
        ),
    )
    mcp_http.add_middleware(Gate)
    mcp_http.add_middleware(RewriteToolStatus)
    return mcp_http
