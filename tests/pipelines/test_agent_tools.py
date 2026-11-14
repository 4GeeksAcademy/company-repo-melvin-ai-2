"""Ticket and inventory questions go through an MCP client. Routing stays visible."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"
API = SERVICES / "api"
for path in (ROOT, SERVICES, API):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent.graph import run_agent
from agent.tools import (
    INVENTORY_UNAVAILABLE,
    TICKET_UNAVAILABLE,
    TOOL_TIMEOUT_SECONDS,
)
from app.incidents.models import IncidentRecord  # noqa: F401
from app.incidents.service import create_incident
from app.inventory.models import Ingredient, IngredientEntry, IngredientExit  # noqa: F401
from data.pipelines.rag import NOT_ENOUGH
from mcps.brasaland_tools.operations import read_stock, read_ticket

LOYALTY = ROOT / "docs" / "company-knowledge-base" / "brasaland-loyalty-program.en.md"
GOLD_FACT = "Gold (50+ points)"


def _engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'agent-tools.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _nodes(result: dict) -> list[str]:
    return [step["node"] for step in result["trace"]]


class ServiceBackedClient:
    """MCP client double. It calls the MCP operations, not a graph shortcut."""

    def __init__(self, engine):
        self.engine = engine

    def call_tool(self, name, arguments):
        with Session(self.engine) as session:
            if name in {"get_incident", "list_incidents"}:
                query = arguments if name == "list_incidents" else {"ticket_id": arguments["ticket_id"]}
                return read_ticket(session, query)
            if name == "read_inventory":
                return read_stock(session, arguments.get("product") or "")
        raise AssertionError(name)


class RejectingClient:
    def call_tool(self, name, _arguments):
        raise AssertionError(f"this question must not call {name}")


def test_agent_does_not_import_the_incident_service():
    tools = (ROOT / "services" / "agent" / "tools.py").read_text(encoding="utf-8")
    graph = (ROOT / "services" / "agent" / "graph.py").read_text(encoding="utf-8")
    assert "get_incident" not in tools
    assert "from app.incidents" not in graph
    assert "default_ticket_lookup" not in graph
    assert "RemoteMCPClient" in graph


def test_ticket_status_comes_from_the_incident_service(tmp_path):
    engine = _engine(tmp_path)
    with Session(engine) as session:
        row = create_incident(
            session,
            {
                "title": "Fryer down",
                "description": "The fryer stopped heating during service.",
                "category": "equipment_failure",
                "status": "open",
                "origin": "branch",
                "branch": "medellin_centro",
            },
        )
        ticket_id = row.id

    def search(_question, **_kwargs):
        raise AssertionError("a ticket question must not search the manuals")

    result = run_agent(
        f"What is the status of ticket {ticket_id}?",
        search=search,
        mcp_client=ServiceBackedClient(engine),
    )

    assert f"Ticket {ticket_id} is open." in result["answer"]
    assert "equipment_failure" in result["answer"]
    assert "branch" in result["answer"]
    assert _nodes(result)[3:5] == ["lookup_ticket", "report_tools"]
    assert "retrieve_context" not in _nodes(result)
    assert "lookup_inventory" not in _nodes(result)


def test_policy_question_uses_the_manuals_and_not_a_tool():
    manual = LOYALTY.read_text(encoding="utf-8")

    def search(_question, **_kwargs):
        return [
            {
                "source_document": "loyalty-program",
                "section": "Program tiers",
                "text": manual,
            }
        ]

    def complete(_system, user):
        if GOLD_FACT not in user:
            return NOT_ENOUGH
        return "You need 50 points to reach Gold tier."

    result = run_agent(
        "How many points do I need for Gold tier?",
        search=search,
        complete=complete,
        mcp_client=RejectingClient(),
    )

    assert "50" in result["answer"]
    assert "lookup_ticket" not in _nodes(result)
    assert "lookup_inventory" not in _nodes(result)
    assert "retrieve_context" in _nodes(result)
    assert "generate_answer" in _nodes(result)


def test_missing_ticket_does_not_invent_a_status(tmp_path):
    engine = _engine(tmp_path)

    result = run_agent(
        "What is the status of ticket 482?",
        mcp_client=ServiceBackedClient(engine),
        search=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a missing ticket must not search the manuals")
        ),
    )

    assert result["answer"] == TICKET_UNAVAILABLE
    assert "open" not in result["answer"]
    assert "resolved" not in result["answer"]


def test_ticket_tool_timeout_uses_the_fallback_and_the_live_limit_is_four_seconds():
    assert TOOL_TIMEOUT_SECONDS == 4

    class SlowClient:
        def call_tool(self, _name, _arguments):
            time.sleep(0.3)
            return {"found": True, "tickets": [{"status": "open"}]}

    result = run_agent(
        "What is the status of ticket 9?",
        mcp_client=SlowClient(),
        tool_timeout=0.05,
        search=lambda *_args, **_kwargs: [],
    )

    assert result["answer"] == TICKET_UNAVAILABLE


def test_stock_question_reads_the_inventory_service(tmp_path):
    engine = _engine(tmp_path)
    with Session(engine) as session:
        beef = Ingredient(
            name="Beef rib",
            sku="BEEF-RIB",
            unit="kg",
            category="protein",
            country="CO",
        )
        session.add(beef)
        session.commit()
        session.refresh(beef)
        session.add(
            IngredientEntry(
                ingredient_id=beef.id,
                quantity=12,
                supplier_name="Andes Proteins",
                location_id=1,
                user_uuid="1",
            )
        )
        session.commit()

    result = run_agent(
        "Do we have beef?",
        mcp_client=ServiceBackedClient(engine),
        search=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a stock question must not search the manuals")
        ),
    )

    assert "Beef rib" in result["answer"]
    assert "12" in result["answer"]
    assert "lookup_inventory" in _nodes(result)
    assert "retrieve_context" not in _nodes(result)
    assert "lookup_ticket" not in _nodes(result)


def test_missing_product_does_not_invent_stock(tmp_path):
    engine = _engine(tmp_path)

    result = run_agent(
        "Do we have saffron?",
        mcp_client=ServiceBackedClient(engine),
        search=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("a missing product must not search the manuals")
        ),
    )

    assert result["answer"] == INVENTORY_UNAVAILABLE
    assert "0" not in result["answer"]
