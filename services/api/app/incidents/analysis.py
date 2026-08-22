"""Shared Brasaland incident CSV validation and metrics (CONTEXT-aligned)."""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


VALID_LOCATIONS = {f"COL-{i:02d}" for i in range(1, 11)} | {
    f"FLA-{i:02d}" for i in range(1, 5)
}
VALID_CATEGORIES = (
    "CUSTOMER_COMPLAINT",
    "EQUIPMENT",
    "SUPPLY",
    "FOOD_QUALITY",
    "STAFF",
)
VALID_STATUSES = ("OPEN", "CLOSED", "DISCARDED")

REQUIRED_HEADERS = (
    "incident_id",
    "date",
    "location_id",
    "category",
    "description",
    "status",
    "customer_id",
    "satisfaction_score",
    "reporter_id",
)

RULE_MISSING_LOCATION = "missing_location_id"
RULE_INVALID_CATEGORY = "invalid_or_missing_category"
RULE_EMPTY_DESCRIPTION = "empty_description"
RULE_MISSING_REPORTER = "missing_reporter_id"
RULE_CLOSED_NO_SCORE = "closed_no_score"
RULE_SCORE_OUT_OF_RANGE = "score_out_of_range"

SCORE_LABELS = {
    1: "Very dissatisfied",
    2: "Dissatisfied",
    3: "Neutral",
    4: "Satisfied",
    5: "Very satisfied",
}


@dataclass
class AnalysisResult:
    source_name: str
    total_rows: int = 0
    valid_rows: list[dict[str, str]] = field(default_factory=list)
    invalid_count: int = 0
    rule_counts: Counter[str] = field(default_factory=Counter)
    category_counts: Counter[str] = field(default_factory=Counter)
    status_counts: Counter[str] = field(default_factory=Counter)
    score_counts: Counter[int] = field(default_factory=Counter)
    closed_with_score: int = 0
    closed_total: int = 0
    average_score: float | None = None


class IncidentAnalysisError(ValueError):
    """Raised when an uploaded or local file cannot be analyzed."""


def _cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _parse_score(raw: str) -> int | None | str:
    value = raw.strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return "invalid"


def classify_row(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []

    location_id = _cell(row, "location_id")
    if not location_id or location_id not in VALID_LOCATIONS:
        reasons.append(RULE_MISSING_LOCATION)

    category = _cell(row, "category")
    if not category or category not in VALID_CATEGORIES:
        reasons.append(RULE_INVALID_CATEGORY)

    description = _cell(row, "description")
    if len(description) < 5:
        reasons.append(RULE_EMPTY_DESCRIPTION)

    reporter_id = _cell(row, "reporter_id")
    if not reporter_id:
        reasons.append(RULE_MISSING_REPORTER)

    status = _cell(row, "status")
    score = _parse_score(_cell(row, "satisfaction_score"))

    if status == "CLOSED" and score is None:
        reasons.append(RULE_CLOSED_NO_SCORE)

    if score == "invalid" or (isinstance(score, int) and not 1 <= score <= 5):
        reasons.append(RULE_SCORE_OUT_OF_RANGE)

    return reasons


def _pct_number(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 1)


def _pct_label(part: int, whole: int) -> str:
    return f"{_pct_number(part, whole):.1f}%"


def analyze_rows(rows: Iterable[dict[str, str]], source_name: str) -> AnalysisResult:
    result = AnalysisResult(source_name=source_name)

    for row in rows:
        result.total_rows += 1
        reasons = classify_row(row)
        if reasons:
            result.invalid_count += 1
            for reason in reasons:
                result.rule_counts[reason] += 1
            continue

        result.valid_rows.append(row)
        result.category_counts[_cell(row, "category")] += 1
        status = _cell(row, "status")
        result.status_counts[status] += 1

        if status == "CLOSED":
            result.closed_total += 1
            score = _parse_score(_cell(row, "satisfaction_score"))
            if isinstance(score, int):
                result.closed_with_score += 1
                result.score_counts[score] += 1

    if result.closed_with_score:
        total = sum(score * count for score, count in result.score_counts.items())
        result.average_score = round(total / result.closed_with_score, 2)

    return result


def _reader_from_text(text: str) -> csv.DictReader:
    if not text or not text.strip():
        raise IncidentAnalysisError("The uploaded file is empty.")

    sample = text.lstrip("\ufeff")
    stream = io.StringIO(sample)
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        raise IncidentAnalysisError("CSV header row is missing.")

    normalized = [(name or "").strip() for name in reader.fieldnames]
    missing = [h for h in REQUIRED_HEADERS if h not in normalized]
    if missing:
        raise IncidentAnalysisError(
            "CSV is missing required columns: " + ", ".join(missing)
        )
    reader.fieldnames = normalized
    return reader


def analyze_text(text: str, source_name: str) -> AnalysisResult:
    reader = _reader_from_text(text)
    return analyze_rows(reader, source_name=source_name)


def analyze_path(csv_path: Path) -> AnalysisResult:
    text = csv_path.read_text(encoding="utf-8")
    return analyze_text(text, source_name=csv_path.name)


def build_export_rows(result: AnalysisResult) -> list[dict[str, Any]]:
    valid_count = len(result.valid_rows)
    rows: list[dict[str, Any]] = [
        {"metric": "total_records", "value": result.total_rows, "percentage": ""},
        {"metric": "valid_records", "value": valid_count, "percentage": ""},
        {"metric": "invalid_records", "value": result.invalid_count, "percentage": ""},
        {
            "metric": "invalid_missing_location_id",
            "value": result.rule_counts[RULE_MISSING_LOCATION],
            "percentage": "",
        },
        {
            "metric": "invalid_or_missing_category",
            "value": result.rule_counts[RULE_INVALID_CATEGORY],
            "percentage": "",
        },
        {
            "metric": "invalid_empty_description",
            "value": result.rule_counts[RULE_EMPTY_DESCRIPTION],
            "percentage": "",
        },
        {
            "metric": "invalid_missing_reporter_id",
            "value": result.rule_counts[RULE_MISSING_REPORTER],
            "percentage": "",
        },
        {
            "metric": "invalid_closed_no_score",
            "value": result.rule_counts[RULE_CLOSED_NO_SCORE],
            "percentage": "",
        },
        {
            "metric": "invalid_score_out_of_range",
            "value": result.rule_counts[RULE_SCORE_OUT_OF_RANGE],
            "percentage": "",
        },
    ]

    for code in VALID_CATEGORIES:
        count = result.category_counts[code]
        rows.append(
            {
                "metric": f"category_{code}",
                "value": count,
                "percentage": f"{_pct_number(count, valid_count):.1f}",
            }
        )

    for code in VALID_STATUSES:
        count = result.status_counts[code]
        rows.append(
            {
                "metric": f"status_{code}",
                "value": count,
                "percentage": f"{_pct_number(count, valid_count):.1f}",
            }
        )

    rows.append(
        {
            "metric": "satisfaction_scored_cases",
            "value": result.closed_with_score,
            "percentage": "",
        }
    )
    rows.append(
        {
            "metric": "satisfaction_average",
            "value": result.average_score if result.average_score is not None else "",
            "percentage": "",
        }
    )
    for score in range(1, 6):
        rows.append(
            {
                "metric": f"satisfaction_score_{score}",
                "value": result.score_counts[score],
                "percentage": "",
            }
        )
    return rows


def export_results_csv_text(result: AnalysisResult) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["metric", "value", "percentage"])
    writer.writeheader()
    writer.writerows(build_export_rows(result))
    return buffer.getvalue()


def result_to_summary(result: AnalysisResult) -> dict[str, Any]:
    valid_count = len(result.valid_rows)
    return {
        "source_file": result.source_name,
        "totals": {
            "total_records": result.total_rows,
            "valid_records": valid_count,
            "invalid_records": result.invalid_count,
        },
        "invalid_breakdown": {
            "missing_location_id": result.rule_counts[RULE_MISSING_LOCATION],
            "invalid_or_missing_category": result.rule_counts[RULE_INVALID_CATEGORY],
            "empty_description": result.rule_counts[RULE_EMPTY_DESCRIPTION],
            "closed_case_no_score": result.rule_counts[RULE_CLOSED_NO_SCORE],
            "missing_reporter_id": result.rule_counts[RULE_MISSING_REPORTER],
            "score_out_of_range": result.rule_counts[RULE_SCORE_OUT_OF_RANGE],
        },
        "by_category": [
            {
                "category": code,
                "count": result.category_counts[code],
                "percentage": _pct_number(result.category_counts[code], valid_count),
            }
            for code in VALID_CATEGORIES
        ],
        "by_status": [
            {
                "status": code,
                "count": result.status_counts[code],
                "percentage": _pct_number(result.status_counts[code], valid_count),
            }
            for code in VALID_STATUSES
        ],
        "satisfaction": {
            "scored_cases": result.closed_with_score,
            "closed_cases": result.closed_total,
            "average_score": result.average_score,
            "by_score": [
                {
                    "score": score,
                    "label": SCORE_LABELS[score],
                    "count": result.score_counts[score],
                }
                for score in range(1, 6)
            ],
        },
    }


# Back-compat aliases used by the CLI
def analyze(csv_path: Path) -> AnalysisResult:
    return analyze_path(csv_path)


def _pct(part: int, whole: int) -> str:
    return _pct_label(part, whole)
