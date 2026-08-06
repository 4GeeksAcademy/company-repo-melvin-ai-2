#!/usr/bin/env python3
"""Brasaland Incident Report Processor — Phase 1 analysis script."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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

RULE_MISSING_LOCATION = "missing_location_id"
RULE_INVALID_CATEGORY = "invalid_or_missing_category"
RULE_EMPTY_DESCRIPTION = "empty_description"
RULE_MISSING_REPORTER = "missing_reporter_id"
RULE_CLOSED_NO_SCORE = "closed_no_score"
RULE_SCORE_OUT_OF_RANGE = "score_out_of_range"


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


def _cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _parse_score(raw: str) -> int | None | str:
    """Return int score, None if blank, or 'invalid' if not parseable."""
    value = raw.strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return "invalid"


def classify_row(row: dict[str, str]) -> list[str]:
    """Return rule ids that make this row invalid (may be empty)."""
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


def analyze(csv_path: Path) -> AnalysisResult:
    result = AnalysisResult(source_name=csv_path.name)

    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
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


def _pct(part: int, whole: int) -> str:
    if whole == 0:
        return "0.0%"
    return f"{(part / whole) * 100:.1f}%"


def print_report(result: AnalysisResult) -> None:
    valid_count = len(result.valid_rows)
    avg = result.average_score if result.average_score is not None else 0.0

    print("=" * 60)
    print("  BRASALAND — INCIDENT REPORT ANALYSIS")
    print(f"  Source file: {result.source_name}")
    print("=" * 60)
    print()
    print(f"TOTAL RECORDS IN FILE .......... {result.total_rows}")
    print(f"  ├─ Valid records ................ {valid_count}")
    print(f"  └─ Invalid / incomplete .......... {result.invalid_count}")
    print()
    print("INVALID RECORDS BREAKDOWN")
    print(
        f"  ├─ Missing location_id ........... "
        f"{result.rule_counts[RULE_MISSING_LOCATION]}"
    )
    print(
        f"  ├─ Invalid or missing category ... "
        f"{result.rule_counts[RULE_INVALID_CATEGORY]}"
    )
    print(
        f"  ├─ Empty description ............. "
        f"{result.rule_counts[RULE_EMPTY_DESCRIPTION]}"
    )
    print(
        f"  └─ Closed case, no score ......... "
        f"{result.rule_counts[RULE_CLOSED_NO_SCORE]}"
    )
    print()
    print("BREAKDOWN BY CATEGORY (valid records)")
    categories = [
        ("CUSTOMER_COMPLAINT", "CUSTOMER_COMPLAINT ..........."),
        ("EQUIPMENT", "EQUIPMENT ...................."),
        ("SUPPLY", "SUPPLY ......................."),
        ("FOOD_QUALITY", "FOOD_QUALITY ................."),
        ("STAFF", "STAFF ........................."),
    ]
    for index, (code, label) in enumerate(categories):
        count = result.category_counts[code]
        branch = "└─" if index == len(categories) - 1 else "├─"
        print(f"  {branch} {label} {count}  ({_pct(count, valid_count)})")
    print()
    print("BREAKDOWN BY STATUS (valid records)")
    statuses = [
        ("OPEN", "OPEN ........................."),
        ("CLOSED", "CLOSED ......................."),
        ("DISCARDED", "DISCARDED ...................."),
    ]
    for index, (code, label) in enumerate(statuses):
        count = result.status_counts[code]
        branch = "└─" if index == len(statuses) - 1 else "├─"
        print(f"  {branch} {label} {count}  ({_pct(count, valid_count)})")
    print()
    print("SATISFACTION INDEX (closed cases)")
    print(f"  Scored cases: {result.closed_with_score} of {result.closed_total}")
    print(f"  Average score: {avg:.2f} / 5.00")
    score_lines = [
        (1, "Score 1 (Very dissatisfied) ..."),
        (2, "Score 2 (Dissatisfied) ........"),
        (3, "Score 3 (Neutral) ............"),
        (4, "Score 4 (Satisfied) .........."),
        (5, "Score 5 (Very satisfied) ......"),
    ]
    for index, (score, label) in enumerate(score_lines):
        count = result.score_counts[score]
        branch = "└─" if index == len(score_lines) - 1 else "├─"
        print(f"  {branch} {label} {count}")
    print()
    print("=" * 60)


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
            "metric": "invalid_closed_no_score",
            "value": result.rule_counts[RULE_CLOSED_NO_SCORE],
            "percentage": "",
        },
    ]

    for code in VALID_CATEGORIES:
        count = result.category_counts[code]
        rows.append(
            {
                "metric": f"category_{code}",
                "value": count,
                "percentage": _pct(count, valid_count).rstrip("%"),
            }
        )

    for code in VALID_STATUSES:
        count = result.status_counts[code]
        rows.append(
            {
                "metric": f"status_{code}",
                "value": count,
                "percentage": _pct(count, valid_count).rstrip("%"),
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


def export_results_csv(result: AnalysisResult, output_path: Path) -> None:
    rows = build_export_rows(result)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value", "percentage"])
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python analyze.py <path-to-incidents.csv>", file=sys.stderr)
        return 1

    csv_path = Path(args[0])
    if not csv_path.is_file():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        return 1

    result = analyze(csv_path)
    print_report(result)

    try:
        answer = input("Export results to CSV? [y / n]: ").strip().lower()
    except EOFError:
        answer = "n"

    if answer == "y":
        output_path = Path("results.csv")
        export_results_csv(result, output_path)
        print(f"Saved {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
