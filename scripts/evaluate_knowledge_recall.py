"""Measure Recall@3 for the Brasaland manual questions.

Requires Qdrant and the two model ids in the environment.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipelines.rag import load_test_questions, recall_at_3, retrieve


def main() -> None:
    questions = load_test_questions()
    retrieved = {question["id"]: retrieve(question["question"], k=5) for question in questions}
    score = recall_at_3(questions, retrieved)
    print(f"Recall@3 {score:.0%} on {len(questions)} questions")
    if score < 0.8:
        raise SystemExit("Recall@3 is below the 80% briefing threshold.")


if __name__ == "__main__":
    main()
