"""Print the intake result for one PDF. This does not start a second API."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipelines.rfp_intake.document import pdf_to_markdown, readability_metrics
from data.pipelines.rfp_intake.graph import analyze_rfp


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: uv run python scripts/reprocess_rfp.py path/to/request.pdf")
    path = Path(sys.argv[1])
    markdown = pdf_to_markdown(path)
    result = analyze_rfp(markdown)
    result["readability"] = readability_metrics(markdown)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
