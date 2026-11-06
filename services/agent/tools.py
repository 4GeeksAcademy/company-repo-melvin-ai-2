"""Routing and spoken answers for the support agent.

Ticket and stock reads happen on the MCP server. This module does not call
the incident service. `plan_sources` still decides manuals versus tools from
the question alone.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict

TOOL_TIMEOUT_SECONDS = 4
TICKET_UNAVAILABLE = "I couldn't confirm that ticket's status right now."
INVENTORY_UNAVAILABLE = "I couldn't confirm that stock level right now."


class TicketQuery(TypedDict, total=False):
    """Tool input. Same filters as GET /api/incidents, plus one ticket id."""

    ticket_id: int | None
    status: str | None
    origin: str | None
    branch: str | None
    category: str | None


class TicketRecord(TypedDict):
    """Tool output. These are the fields the incident service already returns."""

    id: int
    title: str
    status: str
    category: str
    origin: str
    branch: str
    created_at: str
    updated_at: str


class TicketLookup(TypedDict):
    found: bool
    tickets: list[TicketRecord]


class InventoryQuery(TypedDict):
    """Tool input for GET /inventory/products. One product name."""

    product: str


class InventoryRecord(TypedDict):
    id: int
    name: str
    sku: str
    unit: str
    current_stock: float


class InventoryLookup(TypedDict):
    found: bool
    products: list[InventoryRecord]


def run_tool(action, timeout: float = TOOL_TIMEOUT_SECONDS):
    """Run one read. A timeout or a service error returns None so the graph can recover."""
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        return pool.submit(action).result(timeout=timeout)
    except Exception:
        return None
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def format_tickets(result: dict) -> str:
    sentences = []
    for ticket in result.get("tickets") or []:
        sentences.append(
            f"Ticket {ticket['id']} is {ticket['status']}. "
            f"Category: {ticket['category']}. Origin: {ticket['origin']}. "
            f"Branch: {ticket['branch']}. "
            f"Opened: {ticket['created_at']}. Updated: {ticket['updated_at']}."
        )
    return " ".join(sentences)


def format_products(result: dict) -> str:
    sentences = []
    for product in result.get("products") or []:
        sentences.append(
            f"{product['name']} ({product['sku']}) has {product['current_stock']} {product['unit']} on hand."
        )
    return " ".join(sentences)


def plan_sources(question: str) -> dict:
    """Decide RAG, ticket, and inventory from the question text alone."""
    import re

    text = question.lower()
    match = re.search(r"(?:ticket|incident)\s*#?\s*(\d+)", text)
    ticket_id = int(match.group(1)) if match else None
    use_ticket = ticket_id is not None or "ticket" in text or "incident" in text
    use_inventory = any(
        word in text for word in ("stock", "inventory", "ingredient", "do we have")
    )
    manual = any(
        word in text
        for word in (
            "point",
            "gold",
            "allergen",
            "waste",
            "supplier",
            "manual",
            "policy",
            "discount",
            "cross-contamination",
        )
    )
    use_rag = manual or not (use_ticket or use_inventory)
    if (use_ticket or use_inventory) and not manual:
        use_rag = False
    filters: TicketQuery = {}
    if ticket_id is not None:
        filters["ticket_id"] = ticket_id
    elif use_ticket:
        for name in ("open", "in_progress", "resolved", "discarded"):
            if name.replace("_", " ") in text or name in text:
                filters["status"] = name
                break
    product = ""
    if "do we have " in text:
        product = text.split("do we have ", 1)[1].strip(" ?.!")
    elif "stock of " in text:
        product = text.split("stock of ", 1)[1].strip(" ?.!")
    sources = [
        name
        for name, enabled in (
            ("ticket", use_ticket),
            ("inventory", use_inventory),
            ("rag", use_rag),
        )
        if enabled
    ]
    return {
        "use_ticket": use_ticket,
        "use_inventory": use_inventory,
        "use_rag": use_rag,
        "ticket_query": filters,
        "product": product,
        "sources": "+".join(sources) or "none",
    }

