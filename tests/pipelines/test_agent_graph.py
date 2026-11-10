"""Support-agent graph: routing is visible, and one answer stays on the briefing."""

from __future__ import annotations

import sys
from pathlib import Path

from langgraph.graph import END, START, StateGraph

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"
for path in (ROOT, SERVICES):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent.graph import EMPTY_QUESTION, AgentState, build_graph, run_agent
from data.pipelines.rag import NOT_ENOUGH

LOYALTY = ROOT / "docs" / "company-knowledge-base" / "brasaland-loyalty-program.en.md"
GOLD_FACT = "Gold (50+ points)"


def _nodes(result: dict) -> list[str]:
    return [step["node"] for step in result["trace"]]


def test_blank_question_stops_before_retrieval():
    def search(_question, **_kwargs):
        raise AssertionError("retrieve must not run for an empty question")

    result = run_agent("   ", search=search)

    assert result["error"] == EMPTY_QUESTION
    assert _nodes(result) == ["receive_question"]
    assert result["checkpoints"]
    assert "retrieve_context" not in _nodes(result)


def test_empty_retrieval_answers_honestly_without_generation():
    def search(_question, **_kwargs):
        return []

    def complete(_system, _user):
        raise AssertionError("generation must not run when retrieval is empty")

    result = run_agent(
        "What is the wifi password?",
        search=search,
        complete=complete,
    )

    assert result["answer"] == NOT_ENOUGH
    assert result["error"] == ""
    assert _nodes(result) == [
        "receive_question",
        "choose_sources",
        "retrieve_context",
        "honest_answer",
        "consider_memory",
    ]
    assert "generate_answer" not in _nodes(result)


def test_gold_tier_answer_stays_grounded_in_the_loyalty_manual():
    manual = LOYALTY.read_text(encoding="utf-8")
    assert GOLD_FACT in manual

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
    )

    assert "50" in result["answer"]
    assert result["error"] == ""
    assert _nodes(result) == [
        "receive_question",
        "choose_sources",
        "retrieve_context",
        "generate_answer",
        "consider_memory",
    ]
    assert len(result["checkpoints"]) >= len(result["trace"])


def test_structural_error_fails_when_the_graph_is_compiled():
    builder = StateGraph(AgentState)
    builder.add_node("receive_question", lambda state: state)
    builder.add_edge(START, "missing")
    try:
        builder.compile()
    except ValueError as exc:
        assert "unknown node" in str(exc)
    else:
        raise AssertionError("compile accepted an edge to a node that does not exist")
    assert END == "__end__"
