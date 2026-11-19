"""Part 3 pauses one department at a time, then writes the final document."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, Session, create_engine

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
for path in (ROOT, API):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.rfp.models import RfpDepartmentSection, RfpTicket
from app.rfp.service import begin_approval, process_draft, resume_approval, ticket_payload
from data.pipelines.rfp_intake.approval import detect_conflicts, run_arbitration_rounds
from data.pipelines.rfp_intake.approval_graph import (
    is_interrupted,
    read_approval,
    resume_department,
    run_arbitration,
    start_department,
)
from data.pipelines.rfp_intake.graph import analyze_rfp

MARKDOWN = """
Client: Andes Tech Solutions
Service: weekly catering
Scope: 220 personas on a 12-month contract
Deadline: reply within 10 business days
Location: Medellín
"""


def _use_checkpoint(monkeypatch, path: Path):
    monkeypatch.setattr("data.pipelines.rfp_intake.approval_graph.CHECKPOINT_PATH", path)


def _section(department_id: str, draft: str, owner: str) -> dict:
    return {
        "department_id": department_id,
        "owner": owner,
        "contact_name": owner,
        "draft_content": draft,
        "evaluation": {},
        "open_questions": [],
        "approval_status": "pending",
    }


def test_one_department_pauses_and_resumes_without_restarting(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    section = _section("marketing", "Camila drafts the brand terms for Andes Tech.", "Camila Ospina")
    start_department("ticket-a", section)
    assert is_interrupted("ticket-a", "marketing")
    paused = read_approval("ticket-a", "marketing")
    assert paused["trace"][0]["agent"] == "offer_approval"
    assert paused["trace"][0]["input"]["department_id"] == "marketing"
    assert "timestamp" in paused["trace"][0]

    resumed = resume_department("ticket-a", "marketing", "approve")

    assert is_interrupted("ticket-a", "marketing") is False
    assert resumed["approval_status"] == "approved"
    assert resumed["approver"] == "Camila Ospina"
    assert resumed["draft_content"] == section["draft_content"]
    assert any(entry["agent"] == "apply_decision" for entry in resumed["trace"])


def test_request_changes_stops_at_the_second_round(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    start_department("ticket-limit", _section("operaciones", "Felipe drafts the kitchen plan.", "Felipe Guerrero"))

    first = resume_department("ticket-limit", "operaciones", "request_changes")
    assert first["approval_rounds"] == 1
    assert is_interrupted("ticket-limit", "operaciones")

    second = resume_department("ticket-limit", "operaciones", "request_changes")
    assert second["approval_rounds"] == 2
    assert second["limit_reached"] is True
    assert second["approval_status"] == "request_changes"
    assert is_interrupted("ticket-limit", "operaciones") is False


def test_arbitration_raises_a_price_the_kitchen_cannot_support():
    sections = [
        _section("operaciones", "The per-event price is USD 4,000 (COP 16,000,000).", "Felipe Guerrero"),
        _section("procurement", "The ingredient cost is USD 10,000 (COP 40,000,000).", "Lucía Fernández"),
    ]
    conflicts = detect_conflicts(sections, {"budget_range": ""})
    assert conflicts[0]["trigger_id"] == "cost-vs-feasibility"
    assert conflicts[0]["arbiter"] == "Camila Ospina"

    result = run_arbitration_rounds(sections, {"budget_range": ""})

    revised = {section["department_id"]: section["draft_content"] for section in result["sections"]}
    assert result["rounds"] == 1
    assert "USD 10,000" in revised["operaciones"]
    assert "COP 40,000,000" in revised["operaciones"]
    assert result["trace"][0]["agent"] == "arbitrate"


def test_arbitration_stops_when_the_breach_remains(monkeypatch):
    def leave_it(conflicts, sections):
        return sections, []

    monkeypatch.setattr("data.pipelines.rfp_intake.approval.apply_arbitration", leave_it)
    sections = [_section("operaciones", "We open in 3 business days.", "Felipe Guerrero")]
    result = run_arbitration_rounds(sections, {})

    assert result["rounds"] == 2
    assert result["conflicts"][0]["trigger_id"] == "setup-sla-breach"
    assert result["conflicts"][0]["arbiter"] == "Felipe Guerrero"


def test_approving_one_department_leaves_the_other_paused(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    start_department("ticket-parallel", _section("marketing", "Brand terms.", "Camila Ospina"))
    start_department("ticket-parallel", _section("operaciones", "Kitchen plan.", "Felipe Guerrero"))

    resume_department("ticket-parallel", "operaciones", "approve")

    assert is_interrupted("ticket-parallel", "marketing")
    assert is_interrupted("ticket-parallel", "operaciones") is False
    assert read_approval("ticket-parallel", "operaciones")["approval_status"] == "approved"
    assert read_approval("ticket-parallel", "marketing")["approval_status"] == "pending"


def test_a_second_ticket_does_not_share_the_checkpoint(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    start_department("ticket-1", _section("marketing", "First ticket.", "Camila Ospina"))
    start_department("ticket-2", _section("marketing", "Second ticket.", "Camila Ospina"))

    resume_department("ticket-1", "marketing", "approve")

    assert is_interrupted("ticket-2", "marketing")
    assert read_approval("ticket-2", "marketing")["draft_content"] == "Second ticket."


def test_setup_breach_is_rewritten_before_the_signature(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    sections = [_section("training", "Jake can certify the menu in 3 business days.", "Jake Morrison")]
    result = run_arbitration("ticket-setup", sections, {})

    revised = result["sections"][0]["draft_content"]
    assert "10 business days" in revised
    assert "3 business days" not in revised
    assert result["applied"][0]["arbiter"] == "Felipe Guerrero"


def test_the_three_parts_finish_only_after_every_signature(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    engine = create_engine(
        f"sqlite:///{tmp_path / 'rfp.db'}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    SQLModel.metadata.create_all(engine, tables=[RfpTicket.__table__, RfpDepartmentSection.__table__])
    analyzed = analyze_rfp(MARKDOWN)
    handoff = dict(analyzed["handoff"])
    handoff["ticket_id"] = "e2e-andes"
    with Session(engine) as session:
        session.add(
            RfpTicket(
                ticket_id="e2e-andes",
                status="intake_complete",
                raw_pdf_path=str(tmp_path / "unused.pdf"),
                client_name=analyzed["metadata"]["client_name"],
                handoff_json=json.dumps(handoff),
                budget_range=analyzed["metadata"].get("budget_range") or "",
            )
        )
        for section in analyzed["sections"]:
            session.add(
                RfpDepartmentSection(
                    ticket_id="e2e-andes",
                    department_id=section["department_id"],
                    contact_name=section["contact_name"],
                    key_aspects="\n".join(section["key_aspects"]),
                    open_questions="\n".join(section["open_questions"]),
                )
            )
        session.commit()
        drafted = process_draft(session, "e2e-andes")
        assert drafted.status == "under_evaluation"
        waiting = begin_approval(session, "e2e-andes")
        payload = ticket_payload(session, waiting)
        assert payload["status"] == "waiting_for_approval"
        assert payload["final_document"] == ""
        department_ids = [section["department_id"] for section in payload["sections"]]
        assert "training" not in department_ids
        assert all(section["awaiting_decision"] for section in payload["sections"])

        resume_approval(session, "e2e-andes", "operaciones", "approve")
        still_waiting = ticket_payload(session, session.get(RfpTicket, "e2e-andes"))
        assert still_waiting["status"] == "waiting_for_approval"

        for department_id in department_ids:
            if department_id == "operaciones":
                continue
            resume_approval(session, "e2e-andes", department_id, "approve")
        finished = ticket_payload(session, session.get(RfpTicket, "e2e-andes"))

    assert finished["status"] == "done"
    assert "Andes Tech Solutions" in finished["final_document"]
    assert "consistent quality" in finished["final_document"]
    assert "Camila Ospina" in finished["final_document"]
    assert "Felipe Guerrero" in finished["final_document"]
    assert "Lucía Fernández" in finished["final_document"]
    assert finished["handoff"]["ticket_id"] == "e2e-andes"
    assert finished["handoff"]["key_aspects"]
    assert finished["trace"]
    assert all("timestamp" in entry and "agent" in entry for entry in finished["trace"])


def test_a_large_contract_waits_for_mariana(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    engine = create_engine(
        f"sqlite:///{tmp_path / 'rfp.db'}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    SQLModel.metadata.create_all(engine, tables=[RfpTicket.__table__, RfpDepartmentSection.__table__])
    with Session(engine) as session:
        session.add(
            RfpTicket(
                ticket_id="sunset-1",
                status="under_evaluation",
                raw_pdf_path="",
                client_name="Sunset Bay Resorts",
                budget_range="$60,000-$75,000",
                handoff_json=json.dumps(
                    {
                        "ticket_id": "sunset-1",
                        "metadata": {"budget_range": "$60,000-$75,000", "client_name": "Sunset Bay Resorts"},
                        "key_aspects": {"marketing": ["Exclusive signature menu."]},
                    }
                ),
            )
        )
        session.add(
            RfpDepartmentSection(
                ticket_id="sunset-1",
                department_id="marketing",
                contact_name="Camila Ospina",
                draft_content="Camila drafts the brand terms. Setup and delivery take 10 business days.",
                approval_status="pending",
            )
        )
        session.commit()
        begin_approval(session, "sunset-1")
        resume_approval(session, "sunset-1", "marketing", "approve")
        waiting = ticket_payload(session, session.get(RfpTicket, "sunset-1"))
        assert waiting["status"] == "waiting_for_approval"
        assert any(section["department_id"] == "ceo" and section["awaiting_decision"] for section in waiting["sections"])
        resume_approval(session, "sunset-1", "ceo", "approve")
        finished = ticket_payload(session, session.get(RfpTicket, "sunset-1"))

    assert finished["status"] == "done"
    assert "Mariana Restrepo" in finished["final_document"]
    assert "USD 60,000" in finished["final_document"]
    assert "COP 240,000,000" in finished["final_document"]


def test_a_rejection_blocks_the_final_document(tmp_path, monkeypatch):
    _use_checkpoint(monkeypatch, tmp_path / "approval.sqlite")
    engine = create_engine(
        f"sqlite:///{tmp_path / 'rfp.db'}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    SQLModel.metadata.create_all(engine, tables=[RfpTicket.__table__, RfpDepartmentSection.__table__])
    with Session(engine) as session:
        session.add(
            RfpTicket(
                ticket_id="reject-1",
                status="under_evaluation",
                raw_pdf_path="",
                client_name="Andes Tech Solutions",
                handoff_json=json.dumps({"ticket_id": "reject-1", "metadata": {}, "key_aspects": {}}),
            )
        )
        session.add(
            RfpDepartmentSection(
                ticket_id="reject-1",
                department_id="marketing",
                contact_name="Camila Ospina",
                draft_content="Camila keeps the brand terms.",
                approval_status="pending",
            )
        )
        session.commit()
        begin_approval(session, "reject-1")
        resume_approval(session, "reject-1", "marketing", "reject")
        payload = ticket_payload(session, session.get(RfpTicket, "reject-1"))

    assert payload["status"] == "waiting_for_approval"
    assert payload["final_document"] == ""
    assert payload["sections"][0]["approval_status"] == "rejected"
    assert payload["sections"][0]["draft_content"] == "Camila keeps the brand terms."
