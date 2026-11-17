"""Turn an uploaded RFP PDF into Markdown, then score that text.

MarkItDown is the preferred converter. Its current release depends on
onnxruntime, which publishes no wheel for Intel macOS, so this step uses
pdfminer.six and wraps the extracted words as Markdown. Agents read that
Markdown. They do not read the PDF.
"""

from __future__ import annotations

import os
from pathlib import Path

NLTK_DIR = Path(__file__).resolve().parent / "nltk_data"


def pdf_to_markdown(path: Path) -> str:
    """Extract the PDF and return Markdown before any agent runs."""
    try:
        from markitdown import MarkItDown

        converted = MarkItDown().convert(str(path))
        text = getattr(converted, "text_content", "") or ""
    except Exception:
        from pdfminer.high_level import extract_text

        text = extract_text(str(path)) or ""
    cleaned = (
        text.replace("\x0c", "\n")
        .replace("(cid:127)", "-")
        .replace("\u2022", "-")
    )
    lines = [line.rstrip() for line in cleaned.splitlines()]
    body = "\n".join(lines).strip()
    if not body:
        return "# RFP\n\n"
    return f"# RFP\n\n{body}\n"


def readability_metrics(markdown: str) -> dict:
    """Flesch-Kincaid and Gunning Fog as a processing-cost signal, not a grade."""
    words = [word for word in markdown.split() if word.strip("#")]
    if len(words) < 30:
        return {"flesch_kincaid": None, "gunning_fog": None}
    os.environ.setdefault("NLTK_DATA", str(NLTK_DIR))
    try:
        import nltk
        from readability import Readability

        try:
            nltk.data.find("tokenizers/punkt_tab/english/")
        except LookupError:
            nltk.download("punkt_tab", download_dir=str(NLTK_DIR), quiet=True)
        scored = Readability(markdown)
        return {
            "flesch_kincaid": _number(scored.flesch_kincaid()),
            "gunning_fog": _number(scored.gunning_fog()),
        }
    except Exception:
        return {"flesch_kincaid": None, "gunning_fog": None}


def _number(value) -> float:
    score = getattr(value, "score", value)
    return round(float(score), 2)
