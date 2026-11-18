"""Upload an RFP and poll its ticket. The graph lives in data/pipelines."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.auth.deps import get_current_user
from app.inventory.db import get_engine
from app.rfp.service import (
    create_ticket,
    list_tickets,
    mark_drafting,
    process_draft,
    process_ticket,
    ticket_payload,
)

logger = logging.getLogger("brasaland.rfp")
router = APIRouter(prefix="/rfp", tags=["rfp-intake"])


def _draft_later(ticket_id: str) -> None:
    try:
        with Session(get_engine()) as session:
            process_draft(session, ticket_id)
    except Exception:
        logger.exception("RFP draft failed for %s", ticket_id)


def _run_later(ticket_id: str) -> None:
    try:
        with Session(get_engine()) as session:
            process_ticket(session, ticket_id)
    except Exception:
        logger.exception("RFP intake failed for %s", ticket_id)


@router.post("/tickets", status_code=202)
async def upload_rfp(
    file: UploadFile,
    background: BackgroundTasks,
    _user=Depends(get_current_user),
) -> dict:
    """Accept the PDF, return the analyzing ticket, and continue in the background."""
    name = (file.filename or "").lower()
    if not name.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload the RFP as a PDF.")
    payload = await file.read()
    if not payload.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="That file is not a PDF.")
    try:
        with Session(get_engine()) as session:
            row = create_ticket(session, payload)
            body = ticket_payload(session, row)
    except Exception:
        logger.exception("RFP upload failed")
        raise HTTPException(
            status_code=503,
            detail="The RFP ticket could not be saved. Try again or contact hello@brasaland.com.",
        ) from None
    background.add_task(_run_later, body["ticket_id"])
    return body


@router.post("/tickets/{ticket_id}/draft", status_code=202)
def start_draft(
    ticket_id: str,
    background: BackgroundTasks,
    _user=Depends(get_current_user),
) -> dict:
    """Start department drafts from the Part 1 handoff."""
    try:
        with Session(get_engine()) as session:
            body = mark_drafting(session, ticket_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="That RFP ticket was not found.") from None
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail="Drafting starts from an intake_complete ticket.",
        ) from None
    background.add_task(_draft_later, ticket_id)
    return body


@router.get("/tickets")
def read_tickets(_user=Depends(get_current_user)) -> dict:
    with Session(get_engine()) as session:
        rows = [ticket_payload(session, row) for row in list_tickets(session)]
    return {"tickets": rows}


@router.get("/tickets/{ticket_id}")
def read_ticket(ticket_id: str, _user=Depends(get_current_user)) -> dict:
    with Session(get_engine()) as session:
        from app.rfp.models import RfpTicket

        row = session.get(RfpTicket, ticket_id)
        if row is None:
            raise HTTPException(status_code=404, detail="That RFP ticket was not found.")
        return ticket_payload(session, row)
