"""RFP intake stays deterministic. The three briefing PDFs decide accept or discard."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
for path in (ROOT, API):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.rfp.models import RfpDepartmentSection, RfpTicket
from app.rfp.service import create_ticket, process_ticket, ticket_payload
from data.pipelines.rfp_intake.analyze import work_department
from data.pipelines.rfp_intake.document import pdf_to_markdown
from data.pipelines.rfp_intake.graph import analyze_rfp

SAMPLES = ROOT / "docs" / "rfp" / "rfp-requests" / "brasaland"


def _markdown(name: str) -> str:
    return pdf_to_markdown(SAMPLES / name)


def test_the_formal_sunset_bay_rfp_uses_all_four_departments():
    result = analyze_rfp(_markdown("brasaland-request-1.pdf"))

    assert result["is_rfp"] is True
    assert result["metadata"]["client_name"].startswith("Sunset Bay Resorts")
    assert "60,000" in result["metadata"]["budget_range"]
    assert result["departments"] == ["marketing", "operaciones", "procurement", "training"]
    assert result["handoff"]["key_aspects"]["training"]
    assert "Camila Ospina" in result["summary"]
    assert "Jake Morrison" in result["summary"]


def test_the_informal_catering_letter_skips_training():
    result = analyze_rfp(_markdown("brasaland-request-2.pdf"))

    assert result["is_rfp"] is True
    assert result["metadata"]["client_name"] == "Andes Tech Solutions"
    assert "training" not in result["departments"]
    assert result["departments"] == ["marketing", "operaciones", "procurement"]
    procurement = work_department(
        "procurement",
        _markdown("brasaland-request-2.pdf"),
        result["metadata"],
    )
    assert "$" not in " ".join(procurement["key_aspects"])
    assert procurement["open_questions"]


def test_the_franchise_inquiry_is_discarded_before_workers():
    result = analyze_rfp(_markdown("brasaland-request-3.pdf"))

    assert result["is_rfp"] is False
    assert "Franchise" in result["discard_reason"]
    assert result.get("sections") in (None, [])
    assert "handoff" not in result


def test_a_department_outside_the_briefing_does_not_get_a_worker():
    markdown = """
    Client: Harbor Hotels
    Service: weekly catering
    Scope: 40 employees on a 6-month contract
    Deadline: reply within 10 business days
    Please also copy the legal department.
    """
    result = analyze_rfp(markdown)
    assert result["is_rfp"] is True
    assert "legal" not in result["departments"]
    assert any("legal department" in question for question in result["open_questions"])


def test_three_pdfs_persist_without_stopping_each_other(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.rfp.service.RAW_DIR",
        tmp_path / "raw",
    )
    engine = create_engine(f"sqlite:///{tmp_path / 'rfp.db'}")
    SQLModel.metadata.create_all(
        engine,
        tables=[RfpTicket.__table__, RfpDepartmentSection.__table__],
    )
    expected = {
        "brasaland-request-1.pdf": "intake_complete",
        "brasaland-request-2.pdf": "intake_complete",
        "brasaland-request-3.pdf": "discarded",
    }
    with Session(engine) as session:
        stored = {}
        for name, status in expected.items():
            row = create_ticket(session, (SAMPLES / name).read_bytes())
            finished = process_ticket(session, row.ticket_id)
            stored[name] = ticket_payload(session, finished)
        assert stored["brasaland-request-1.pdf"]["status"] == "intake_complete"
        assert stored["brasaland-request-2.pdf"]["status"] == "intake_complete"
        assert stored["brasaland-request-3.pdf"]["status"] == "discarded"
        assert stored["brasaland-request-1.pdf"]["handoff"]["ticket_id"]
        assert stored["brasaland-request-1.pdf"]["flesch_kincaid"] is not None
        assert stored["brasaland-request-3.pdf"]["sections"] == []
