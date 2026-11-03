"""Index the four Brasaland manuals in Qdrant.

    uv run python scripts/index_knowledge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.process.rag import setup


def main() -> None:
    count = setup()
    print(f"Indexed {count} chunks in brasaland_knowledge.")


if __name__ == "__main__":
    main()
