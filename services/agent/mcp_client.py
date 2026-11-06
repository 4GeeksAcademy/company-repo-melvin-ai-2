"""Call the Brasaland MCP server. The graph does not open the incident database."""

from __future__ import annotations

import asyncio
import json
import os


class RemoteMCPClient:
    """One Streamable HTTP session per tool call, with the bearer token from the environment."""

    def call_tool(self, name: str, arguments: dict) -> dict | None:
        return asyncio.run(self._call(name, arguments))

    async def _call(self, name: str, arguments: dict) -> dict | None:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        url = os.environ.get("BRASALAND_MCP_URL", "http://127.0.0.1:8765/mcp")
        token = os.environ.get("BRASALAND_MCP_TOKEN", "").strip()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        client = MultiServerMCPClient(
            {
                "brasaland": {
                    "transport": "http",
                    "url": url,
                    "headers": headers,
                }
            }
        )
        async with client.session("brasaland") as session:
            result = await session.call_tool(name, arguments or {})
        if getattr(result, "isError", False):
            return None
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict) and ("tickets" in structured or "products" in structured):
            return structured
        content = getattr(result, "content", None) or []
        if not content:
            return structured if isinstance(structured, dict) else None
        text = getattr(content[0], "text", "") or ""
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict) and "result" in payload and isinstance(payload["result"], dict):
            payload = payload["result"]
        return payload if isinstance(payload, dict) else None
