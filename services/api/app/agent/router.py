"""Ask the compiled support agent. This module does not search or generate."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[4]
SERVICES = ROOT / "services"
for path in (str(ROOT), str(SERVICES)):
    if path not in sys.path:
        sys.path.insert(0, path)

from agent.graph import run_agent  # noqa: E402
from services.agent.guardrails import summary as guardrail_summary  # noqa: E402
from app.auth.deps import get_current_user  # noqa: E402

logger = logging.getLogger("brasaland.agent")
router = APIRouter(prefix="/agent", tags=["support-agent"])

UNAVAILABLE = (
    "The knowledge assistant is unavailable. Try again or contact hello@brasaland.com."
)


class AgentQuestion(BaseModel):
    question: str = Field(max_length=500)
    thread_id: str | None = None


class AgentAnswer(BaseModel):
    answer: str
    thread_id: str


class GuardrailSummary(BaseModel):
    structural: int
    content: int
    security: int
    guardrails: dict[str, int]


@router.get("/guardrails", response_model=GuardrailSummary)
def read_guardrails(_user=Depends(get_current_user)) -> GuardrailSummary:
    """Counts for this process: structural, content, and security."""
    return GuardrailSummary(**guardrail_summary())


@router.post("/query", response_model=AgentAnswer)
def ask_agent(body: AgentQuestion, _user=Depends(get_current_user)) -> AgentAnswer:
    try:
        result = run_agent(body.question, thread_id=body.thread_id)
    except Exception:
        logger.exception("Support agent failed")
        raise HTTPException(status_code=503, detail=UNAVAILABLE) from None
    if result.get("error"):
        raise HTTPException(status_code=400, detail=str(result["error"]))
    return AgentAnswer(
        answer=str(result.get("answer") or ""),
        thread_id=str(result.get("thread_id") or ""),
    )
