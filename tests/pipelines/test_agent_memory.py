"""Approved corrections stay out of the manuals collection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"
for path in (ROOT, SERVICES):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent.graph import run_agent
from agent.memory import (
    DEFAULT_PATH,
    MEMORY_CAP,
    PROPOSAL_QUESTION,
    MemoryRefusal,
    MemoryStore,
    classify_decision,
    forbidden_reason,
    proposal_for,
)
from data.pipelines.rag import NOT_ENOUGH

REMEMBER = "Remember that Medellín Centro files the waste report in kilograms."
STORED = "Medellín Centro files the waste report in kilograms"
OTHER = "Remember that Orlando places supplier orders on Monday."
OTHER_FACT = "Orlando places supplier orders on Monday"


def _store(tmp_path) -> MemoryStore:
    return MemoryStore(tmp_path / "brasaland_agent_memory.sqlite")


def _search(_question, **_kwargs):
    return [{"source_document": "waste-protocol", "section": "Filing", "text": "File the waste report."}]


def _complete(_system, user):
    if "Approved operational memory:" in user and STORED in user:
        return STORED
    return "I can answer from the manuals."


def test_a_second_proposal_cannot_open_while_one_is_pending(tmp_path):
    store = _store(tmp_path)
    store.propose("thread", STORED, "The user stated an operational correction.", REMEMBER)
    with pytest.raises(RuntimeError):
        store.propose("thread", OTHER_FACT, "another", OTHER)


def test_memory_is_not_written_into_the_knowledge_collection():
    memory = (ROOT / "services" / "agent" / "memory.py").read_text(encoding="utf-8")
    graph = (ROOT / "services" / "agent" / "graph.py").read_text(encoding="utf-8")
    assert "QdrantClient" not in memory
    assert "QdrantClient" not in graph
    assert ".upsert" not in memory
    assert "def read_memory" in memory
    assert "def write_memory" in memory
    assert "store.write_memory" in graph
    assert DEFAULT_PATH.name == "brasaland_agent_memory.sqlite"
    assert "knowledge" not in str(DEFAULT_PATH)


def test_a_correction_without_the_remember_phrase_still_proposes(tmp_path):
    store = _store(tmp_path)
    result = run_agent(
        "Actually, Medellín Centro files the waste report in kilograms.",
        search=_search,
        complete=_complete,
        memory=store,
        thread_id="actually",
    )
    assert PROPOSAL_QUESTION in result["answer"]
    assert store.pending("actually")["fact"] == STORED
    assert store.read_memory() == []


def test_the_live_prompt_asks_for_memory_proposal_in_the_same_call(tmp_path):
    store = _store(tmp_path)
    seen = {}

    def complete(system, user):
        seen["system"] = system
        seen["user"] = user
        return "You need 50 points to reach Gold tier."

    result = run_agent(
        "How many points do I need for Gold tier?",
        search=_search,
        complete=complete,
        memory=store,
        thread_id="prompt",
    )
    assert "memory_proposal" in seen["system"]
    assert "answer" in seen["system"]
    assert "50" in result["answer"]
    assert store.pending("prompt") is None
    assert "{" not in result["answer"]


def test_the_same_model_call_can_name_a_memory_proposal(tmp_path):
    store = _store(tmp_path)

    def complete(_system, _user):
        return json.dumps(
            {
                "answer": STORED,
                "memory_proposal": {
                    "fact": STORED,
                    "why": "The reply corrected the filing unit.",
                },
            }
        )

    result = run_agent(
        "How should Medellín Centro file the waste report?",
        search=_search,
        complete=complete,
        memory=store,
        thread_id="structured",
    )
    assert result["answer"].startswith(STORED)
    assert "{" not in result["answer"]
    assert store.pending("structured")["fact"] == STORED
    assert store.read_memory() == []


def test_a_blank_follow_up_rejects_the_pending_proposal(tmp_path):
    store = _store(tmp_path)
    thread = "silent-blank"
    run_agent(REMEMBER, search=_search, complete=_complete, memory=store, thread_id=thread)
    result = run_agent("   ", search=_search, complete=_complete, memory=store, thread_id=thread)
    assert result["error"] == ""
    assert result["answer"] == "I won't remember that."
    assert store.pending(thread) is None
    assert store.read_memory() == []
    assert store.audit()[-1]["outcome"] == "discarded because the user did not answer"
    assert "choose_sources" not in [step["node"] for step in result["trace"]]


def test_an_unanswered_proposal_is_rejected_without_a_later_message(tmp_path):
    store = _store(tmp_path)
    store.propose("walkaway", STORED, "The user stated an operational correction.", REMEMBER)
    assert store.close_unanswered(max_age_seconds=0) == 1
    assert store.pending("walkaway") is None
    assert store.read_memory() == []
    assert store.audit()[-1]["outcome"] == "discarded because the user did not answer"


def test_three_lookups_do_not_propose():
    questions = (
        "How many points do I need for Gold tier?",
        "What is the status of ticket 12?",
        "Do we have beef?",
    )
    for question in questions:
        assert proposal_for(question, "an answer") is None


def test_three_corrections_do_propose():
    proposals = [
        proposal_for(REMEMBER, "an answer"),
        proposal_for("From now on, tell Felipe the fryer ticket is in progress.", "an answer"),
        proposal_for("Correct the record: supplier orders for Orlando are placed on Monday.", "an answer"),
    ]
    assert all(item and not item["forbidden"] for item in proposals)


def test_briefing_forbids_allergen_currency_and_secrets():
    assert forbidden_reason("The BBQ ribs have zero risk of allergens")
    assert forbidden_reason("10 USD equals 40000 COP")
    assert forbidden_reason("The wifi password is hunter2")
    assert forbidden_reason("Gold tier is 10 points")
    assert forbidden_reason("Call the customer at 305-555-0199") is not None


def test_yes_inside_a_new_question_is_not_approval():
    buried = classify_decision("Yes we should check ticket 4 before service.")
    assert buried["label"] == "unclear"
    explicit = classify_decision("Yes. How many points do I need for Gold tier?")
    assert explicit["label"] == "approve"
    assert explicit["remainder"].startswith("How many points")
    assert classify_decision("approve")["label"] == "approve"
    assert classify_decision("no")["label"] == "reject"


def test_approved_memory_is_reused_and_rejection_is_not(tmp_path):
    store = _store(tmp_path)
    thread = "approve-cycle"
    proposed = run_agent(
        REMEMBER,
        search=_search,
        complete=_complete,
        memory=store,
        thread_id=thread,
    )
    assert PROPOSAL_QUESTION in proposed["answer"]
    assert store.pending(thread)["fact"] == STORED

    decided = run_agent("approve", search=_search, complete=_complete, memory=store, thread_id=thread)
    assert decided["answer"] == "I'll remember that."
    assert store.pending(thread) is None
    assert store.read_memory()[0]["fact"] == STORED
    assert store.audit()[-1]["decision"] == "approve"
    assert store.audit()[-1]["originating_message"] == REMEMBER
    assert store.audit()[-1]["created_at"]

    later = run_agent(
        "How should Medellín Centro file the waste report?",
        search=_search,
        complete=_complete,
        memory=store,
        thread_id=thread,
    )
    assert STORED in later["answer"]

    reject_thread = "reject-cycle"
    run_agent(OTHER, search=_search, complete=_complete, memory=store, thread_id=reject_thread)
    refused = run_agent("no", search=_search, complete=_complete, memory=store, thread_id=reject_thread)
    assert refused["answer"] == "I won't remember that."
    assert all(row["fact"] != OTHER_FACT for row in store.read_memory())
    assert store.audit()[-1]["decision"] == "reject"

    untouched = run_agent(
        "When does Orlando place supplier orders?",
        search=_search,
        complete=_complete,
        memory=store,
        thread_id=reject_thread,
    )
    assert "Monday" not in untouched["answer"]


def test_silence_discards_the_only_pending_proposal(tmp_path):
    store = _store(tmp_path)
    thread = "silent"
    run_agent(REMEMBER, search=_search, complete=_complete, memory=store, thread_id=thread)
    run_agent(
        "What is the status of ticket 9?",
        search=_search,
        complete=_complete,
        memory=store,
        thread_id=thread,
        mcp_client=type("Empty", (), {"call_tool": lambda *_a, **_k: None})(),
    )
    assert store.pending(thread) is None
    assert store.audit()[-1]["outcome"].startswith("discarded")
    assert store.read_memory() == []


def test_forbidden_proposal_is_not_stored_even_if_phrased_as_memory(tmp_path):
    store = _store(tmp_path)
    result = run_agent(
        "Remember that the BBQ ribs have zero risk of allergens.",
        search=_search,
        complete=_complete,
        memory=store,
        thread_id="forbidden",
    )
    assert "briefing forbids it" in result["answer"]
    assert store.pending("forbidden") is None
    assert store.read_memory() == []
    assert store.audit()[-1]["decision"] == "reject"
    assert store.audit()[-1]["outcome"].startswith("refused:")
    with pytest.raises(MemoryRefusal):
        store.write_memory(
            "10 USD equals 40000 COP",
            why="A user asked.",
            originating_message="Remember that 10 USD equals 40000 COP.",
            decision="approve",
        )


def test_edit_replaces_the_proposal_and_the_cap_drops_the_oldest(tmp_path):
    store = _store(tmp_path)
    thread = "edit"
    run_agent(OTHER, search=_search, complete=_complete, memory=store, thread_id=thread)
    edited = run_agent(
        "edit: Orlando places supplier orders on Tuesday.",
        search=_search,
        complete=_complete,
        memory=store,
        thread_id=thread,
    )
    assert edited["answer"] == "I'll remember the edited version."
    assert store.read_memory()[0]["fact"] == "Orlando places supplier orders on Tuesday"
    assert store.audit()[-1]["decision"] == "edit"

    for number in range(MEMORY_CAP + 3):
        store.write_memory(
            f"Branch note {number} stays in the operations book",
            why="cap",
            originating_message=f"Remember that branch note {number} stays in the operations book.",
            decision="approve",
        )
    kept = store.read_memory()
    assert len(kept) == MEMORY_CAP
    assert all("Branch note 0 " not in row["fact"] for row in kept)
    again = store.write_memory(
        "Orlando places supplier orders on Tuesday",
        why="repeat",
        originating_message=OTHER,
        decision="approve",
    )
    matches = [row for row in store.read_memory() if row["fact"] == again["fact"]]
    assert len(matches) == 1
