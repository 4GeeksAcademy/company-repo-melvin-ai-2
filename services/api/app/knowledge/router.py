"""Ask the Brasaland manuals. The response is the generated answer only."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth.deps import get_current_user  # noqa: E402
from data.pipelines.rag import query  # noqa: E402

logger = logging.getLogger("brasaland.knowledge")
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class KnowledgeAnswer(BaseModel):
    answer: str


@router.post("/query", response_model=KnowledgeAnswer)
def ask_knowledge(body: KnowledgeQuestion, _user=Depends(get_current_user)) -> KnowledgeAnswer:
    try:
        answer = query(body.question.strip())
    except Exception:
        logger.exception("Knowledge query failed")
        raise HTTPException(
            status_code=503,
            detail="The knowledge assistant is unavailable. Try again or contact hello@brasaland.com.",
        ) from None
    return KnowledgeAnswer(answer=answer)
