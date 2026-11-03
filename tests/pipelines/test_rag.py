"""Brasaland manual assistant: chunks stay whole, and the answer is generated."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipelines.rag import generate_answer, query, recall_at_3, retrieve
from data.process.rag import KNOWLEDGE_DIR, SOURCE_SLUGS, chunk_id, load_chunks, semantic_chunks

KNOWLEDGE = KNOWLEDGE_DIR


class _Point:
    def __init__(self, score: float, payload: dict) -> None:
        self.score = score
        self.payload = payload


class _Hits:
    def __init__(self, points: list[_Point]) -> None:
        self.points = points


class _Qdrant:
    def __init__(self, points: list[_Point]) -> None:
        self.points = points

    def query_points(self, **_kwargs):
        return _Hits(self.points)


def test_each_manual_becomes_at_least_three_whole_chunks():
    chunks = load_chunks(KNOWLEDGE)
    by_source: dict[str, list[dict]] = {}
    for chunk in chunks:
        by_source.setdefault(chunk["source_document"], []).append(chunk)
        assert chunk["company"] == "brasaland"
        assert chunk["language"] == "en"
        assert chunk["section"]
        assert chunk["text"]

    assert set(by_source) == set(SOURCE_SLUGS.values())
    for source, rows in by_source.items():
        assert len(rows) >= 3, source
        assert [row["chunk_index"] for row in rows] == list(range(len(rows)))

    loyalty = Path(KNOWLEDGE / "brasaland-loyalty-program.en.md").read_text(encoding="utf-8")
    sections = semantic_chunks(loyalty)
    joined = "\n".join(body for _, body in sections)
    assert "Gold (50+ points)" in joined
    assert "20,000 COP (20 USD)" in joined
    assert chunk_id("loyalty-program", 0) == chunk_id("loyalty-program", 0)


def test_retrieve_drops_neighbors_below_the_minimum_score():
    client = _Qdrant(
        [
            _Point(0.91, {"source_document": "loyalty-program", "section": "Tiers", "text": "Gold"}),
            _Point(0.20, {"source_document": "waste-protocol", "section": "Target", "text": "4%"}),
            _Point(0.50, {"source_document": "menu-allergens", "section": "Ribs", "text": "soy"}),
        ]
    )
    hits = retrieve("gold tier", k=5, min_score=0.35, client=client, embedder=lambda _text: [0.1, 0.2])

    assert len(hits) == 2
    assert hits[0]["text"] == "Gold"
    assert all("score" not in hit for hit in hits)
    assert all(hit["text"] != "4%" for hit in hits)


def test_query_returns_the_model_answer_and_not_the_raw_chunk():
    def search(_question, **_kwargs):
        return [{"source_document": "menu-allergens", "section": "Ribs", "text": "SECRET CHUNK soy"}]

    answer = query(
        "Does BBQ Ribs have allergens?",
        search=search,
        complete=lambda _system, _user: "The BBQ Ribs sauce contains soy.",
    )

    assert answer == "The BBQ Ribs sauce contains soy."
    assert "SECRET CHUNK" not in answer


def test_empty_retrieval_still_goes_through_generation():
    seen = {}

    def complete(system, user):
        seen["user"] = user
        return "The Brasaland manuals do not contain enough information to answer that."

    answer = generate_answer("What is the wifi password?", [], complete=complete)

    assert "No manual excerpt" in seen["user"]
    assert answer.startswith("The Brasaland manuals do not contain enough information")


def test_recall_at_3_counts_only_the_expected_phrase_in_the_top_three():
    questions = [
        {"id": "gold", "expected_source": "loyalty-program", "expected_phrase": "Gold (50+ points)"},
        {"id": "waste", "expected_source": "waste-protocol", "expected_phrase": "below 4%"},
    ]
    retrieved = {
        "gold": [
            {"source_document": "waste-protocol", "text": "other"},
            {"source_document": "loyalty-program", "text": "Gold (50+ points): 15% permanent discount"},
        ],
        "waste": [
            {"source_document": "waste-protocol", "text": "unrelated"},
            {"source_document": "waste-protocol", "text": "still unrelated"},
            {"source_document": "waste-protocol", "text": "still unrelated"},
            {"source_document": "waste-protocol", "text": "below 4% of monthly ingredient cost"},
        ],
    }

    assert recall_at_3(questions, retrieved) == 0.5
