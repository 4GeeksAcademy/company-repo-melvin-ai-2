"""Part 2 drafts from the Part 1 handoff and keeps a section that cannot pass."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, Session, create_engine

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
for path in (ROOT, API):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.rfp.models import RfpDepartmentSection, RfpTicket
from app.rfp.service import process_draft
from data.pipelines.rfp_intake import draft as draft_mod
from data.pipelines.rfp_intake.draft import (
    evaluate_compliance,
    evaluate_readability,
    evaluation_result,
    generate_marketing,
)
from data.pipelines.rfp_intake.draft_graph import draft_from_handoff

SHORT_SETUP = (
    "We will open the kitchen for this client in 3 business days and start service immediately. "
    * 4
)


def _handoff() -> dict:
    return {
        "ticket_id": "ticket-1",
        "status": "intake_complete",
        "metadata": {
            "client_name": "Andes Tech Solutions",
            "location": "Medellín",
            "service_type": "weekly catering",
            "scope": "220 personas",
            "deadline": "antes del 18 de agosto",
            "budget_range": "",
        },
        "key_aspects": {
            "marketing": ["Weekly catering for the Medellín office."],
            "operaciones": ["About 220 people on Tuesday and Thursday."],
        },
        "contacts": {
            "marketing": "Camila Ospina",
            "operaciones": "Felipe Guerrero",
        },
        "summary": "Camila can brief the departments.",
        "open_questions": [],
        "conflicts": [],
    }


def test_marketing_generator_covers_the_briefing_rules():
    text = generate_marketing(
        {
            "metadata": {
                "client_name": "Sunset Bay Resorts",
                "location": "Florida",
                "service_type": "co-branded concession",
                "budget_range": "$60,000–$75,000",
            },
            "key_aspects": ["Exclusive signature menu for Sunset Bay."],
            "open_questions": [],
            "feedback": "",
        }
    )
    result = evaluation_result("marketing", text, ["Exclusive signature menu for Sunset Bay."])

    assert "Camila Ospina" in text
    assert "Exclusive signature menu for Sunset Bay." in text
    assert "USD 60,000" in text
    assert "COP 240,000,000" in text
    assert result["overall_pass"] is True
    assert result["readability"]["pass"] is True
    assert result["relevance"]["missing_aspects"] == []
    assert result["compliance"]["pass"] is True
    assert result["feedback_for_generator"] == ""


def test_a_short_section_fails_readability():
    result = evaluate_readability("Too short to score.")

    assert result["pass"] is False
    assert result["score"] is None


def test_compliance_fails_when_setup_is_under_10_business_days():
    result = evaluate_compliance(SHORT_SETUP)

    assert result["pass"] is False
    assert "setup-sla" in result["rule_ids"]
    assert any(item["rule_id"] == "setup-sla" for item in result["violations"])
    assert "10 business days" in result["violations"][0]["message"] or any(
        "10 business days" in item["message"] for item in result["violations"]
    )


def test_a_failed_draft_is_revised_once_and_then_passes():
    calls = {"n": 0}
    real = draft_mod.generate_marketing

    def first_draft_is_too_fast(state):
        calls["n"] += 1
        if calls["n"] == 1:
            return SHORT_SETUP
        return real(state)

    draft_mod.generate_marketing = first_draft_is_too_fast
    try:
        drafted = draft_from_handoff(
            {
                **_handoff(),
                "key_aspects": {"marketing": ["Weekly catering for the Medellín office."]},
            }
        )
    finally:
        draft_mod.generate_marketing = real

    section = drafted["sections"][0]
    assert section["iterations"] == 2
    assert section["approval_status"] == "pending"
    assert section["evaluation"]["overall_pass"] is True
    assert "10 business days" in section["draft_content"]
    assert drafted["status"] == "under_evaluation"


def test_departments_run_together_and_a_stuck_section_is_kept():
    barrier = threading.Barrier(2)
    entered = {"marketing": 0, "operaciones": 0}
    real_marketing = draft_mod.generate_marketing
    real_operaciones = draft_mod.generate_operaciones

    def marketing(state):
        entered["marketing"] += 1
        if entered["marketing"] == 1:
            barrier.wait(timeout=2)
        return real_marketing(state)

    def operaciones(state):
        entered["operaciones"] += 1
        if entered["operaciones"] == 1:
            barrier.wait(timeout=2)
        return SHORT_SETUP

    draft_mod.generate_marketing = marketing
    draft_mod.generate_operaciones = operaciones
    try:
        drafted = draft_from_handoff(_handoff())
    finally:
        draft_mod.generate_marketing = real_marketing
        draft_mod.generate_operaciones = real_operaciones

    by_id = {section["department_id"]: section for section in drafted["sections"]}
    assert entered["marketing"] == 1
    assert entered["operaciones"] == 3
    assert by_id["marketing"]["approval_status"] == "pending"
    assert by_id["operaciones"]["approval_status"] == "needs_human_review"
    assert by_id["operaciones"]["draft_content"] == SHORT_SETUP
    assert by_id["operaciones"]["evaluation"]["overall_pass"] is False
    assert "3 business days" in by_id["operaciones"]["evaluation"]["feedback_for_generator"]
    assert drafted["status"] == "needs_human_review"
    assert drafted["handoff"]["ticket_id"] == "ticket-1"
    assert drafted["handoff"]["key_aspects"]["marketing"]


def test_process_draft_stores_the_handoff_without_rereading_the_pdf(tmp_path, monkeypatch):
    def fail_if_called(_path):
        raise AssertionError("Part 2 must not read the PDF.")

    monkeypatch.setattr("data.pipelines.rfp_intake.document.pdf_to_markdown", fail_if_called)
    engine = create_engine(
        f"sqlite:///{tmp_path / 'rfp.db'}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    SQLModel.metadata.create_all(
        engine,
        tables=[RfpTicket.__table__, RfpDepartmentSection.__table__],
    )
    handoff = _handoff()
    seen = []
    real_mark = __import__("app.rfp.service", fromlist=["_mark"])._mark

    def spy(session, ticket_id, status, only_from=None):
        seen.append(status)
        return real_mark(session, ticket_id, status, only_from=only_from)

    monkeypatch.setattr("app.rfp.service._mark", spy)
    with Session(engine) as session:
        session.add(
            RfpTicket(
                ticket_id="ticket-1",
                status="intake_complete",
                raw_pdf_path=str(tmp_path / "missing.pdf"),
                handoff_json=json.dumps(handoff),
                client_name="Andes Tech Solutions",
            )
        )
        session.add(
            RfpDepartmentSection(
                ticket_id="ticket-1",
                department_id="marketing",
                key_aspects="Weekly catering for the Medellín office.",
                contact_name="Camila Ospina",
                open_questions="The RFP does not state an exclusivity or brand term.",
            )
        )
        session.add(
            RfpDepartmentSection(
                ticket_id="ticket-1",
                department_id="operaciones",
                key_aspects="About 220 people on Tuesday and Thursday.",
                contact_name="Felipe Guerrero",
            )
        )
        session.commit()
        finished = process_draft(session, "ticket-1")
        from app.rfp.service import ticket_payload

        payload = ticket_payload(session, finished)

    assert "drafting" in seen
    assert "under_evaluation" in seen
    assert payload["status"] == "under_evaluation"
    assert payload["sections"][0]["draft_content"]
    assert payload["sections"][0]["evaluation"]["overall_pass"] is True
    assert payload["sections"][0]["approval_status"] == "pending"
    assert "exclusivity" in payload["sections"][0]["draft_content"]
    assert payload["handoff"]["sections"][0]["draft_content"]
    assert "section_questions" not in payload["handoff"]
