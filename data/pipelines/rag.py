"""Retrieve Brasaland manual excerpts and have a generation model answer from them.

`query` is the only function the API calls. It does not return raw search hits.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from data.process.rag import COLLECTION, embed, model_settings

logger = logging.getLogger("brasaland.knowledge")

NOT_ENOUGH = (
    "The Brasaland manuals do not contain enough information to answer that."
)

_SYSTEM = """You answer as a trained Brasaland salesperson helping a location manager.
Use only the manual excerpts. Be confident when the excerpt states the fact, and do not add policies, prices, allergens, or amounts that are not written there.
If the excerpts do not contain the answer, reply with exactly: The Brasaland manuals do not contain enough information to answer that.
Never say there is zero risk of cross-contamination, and never guarantee a dish is allergen-free beyond the excerpt.
Keep peso and dollar amounts exactly as written. Do not convert currency.
Answer in English."""

_MEMORY_FIELD = """
Return one JSON object and nothing else, with this shape:
{"answer": "the sentence the location manager should read", "memory_proposal": null}
Set memory_proposal to {"fact": "the operational correction", "why": "why it is worth keeping"} only when this turn states a new correction that is not already in the manuals.
Use null for a greeting, a manual lookup, a ticket lookup, or a stock lookup.
Do not propose allergen zero risk, a currency conversion, a password, a phone number, an email address, or a points or money figure.
"""


def minimum_score() -> float:
    """Cosine similarity floor. Neighbors below this are treated as a miss."""
    raw = os.environ.get("RAG_MIN_SCORE", "0.35")
    return float(raw)


def retrieve(query: str, *, k: int = 5, min_score: float | None = None, client=None, embedder=None) -> list[dict]:
    """Embed the question, keep neighbors at or above `min_score`, and return payloads."""
    floor = minimum_score() if min_score is None else min_score
    vector = (embedder or embed)(query)
    qdrant = client or _connect()
    found = qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=k,
        with_payload=True,
    )
    hits = []
    for point in found.points:
        if float(point.score) < floor:
            continue
        payload = dict(point.payload or {})
        hits.append(payload)
    logger.info("knowledge retrieve kept %s of %s hits", len(hits), len(found.points))
    return hits


def generate_answer(question: str, context: list[dict], *, complete=None, memory_field: bool = False) -> str:
    """Ask the generation model to speak from the retrieved excerpts only.

    The support agent sets `memory_field` so the same call also returns `memory_proposal`.
    The manuals endpoint leaves it off and still receives a plain answer.
    """
    excerpts = "\n\n".join(
        f"[{item.get('source_document')} / {item.get('section')}]\n{item.get('text', '')}"
        for item in context
    )
    if not excerpts:
        excerpts = "No manual excerpt cleared the similarity threshold."
    user = f"Manual excerpts:\n{excerpts}\n\nQuestion: {question}"
    system = _SYSTEM + _MEMORY_FIELD if memory_field else _SYSTEM
    reply = (complete or chat_complete)(system, user)
    text = reply.strip()
    if not text:
        return NOT_ENOUGH
    return text


def query(question: str, *, search=None, complete=None) -> str:
    """Search, then generate. Callers receive the answer string and nothing else."""
    hits = (search or retrieve)(question, k=5, min_score=minimum_score())
    return generate_answer(question, hits, complete=complete)


def chat_complete(system: str, user: str) -> str:
    """Call the generation model. This path does not request an embedding."""
    settings = model_settings()
    from data.process.rag import _post_json

    payload = _post_json(
        f"{settings.base_url}/chat/completions",
        settings.api_key,
        {
            "model": settings.generation_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    return payload["choices"][0]["message"]["content"]


def recall_at_3(questions: list[dict], retrieved: dict[str, list[dict]]) -> float:
    """Share of questions whose expected phrase is in the top 3 chunks."""
    if not questions:
        return 0.0
    found = 0
    for question in questions:
        top = retrieved.get(question["id"], [])[:3]
        phrase = question["expected_phrase"].lower()
        source = question["expected_source"]
        if any(
            item.get("source_document") == source and phrase in str(item.get("text", "")).lower()
            for item in top
        ):
            found += 1
    return found / len(questions)


def _connect():
    from data.process.rag import connect_qdrant

    return connect_qdrant()


def load_test_questions() -> list[dict]:
    path = os.environ.get("RAG_TEST_QUERIES")
    file_path = Path(path) if path else Path(__file__).resolve().parents[2] / "data" / "eval" / "test-queries.json"
    return json.loads(file_path.read_text(encoding="utf-8"))
