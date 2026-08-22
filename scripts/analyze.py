#!/usr/bin/env python3
"""Brasaland Incident Report Processor — Phase 1 CLI (uses shared API analysis)."""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1] / "services" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.incidents.analysis import (  # noqa: E402
    RULE_CLOSED_NO_SCORE,
    RULE_EMPTY_DESCRIPTION,
    RULE_INVALID_CATEGORY,
    RULE_MISSING_LOCATION,
    RULE_MISSING_REPORTER,
    RULE_SCORE_OUT_OF_RANGE,
    AnalysisResult,
    analyze_path,
    export_results_csv_text,
    _pct_label,
)


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
        f"  ├─ Missing reporter_id ........... "
        f"{result.rule_counts[RULE_MISSING_REPORTER]}"
    )
    print(
        f"  ├─ Closed case, no score ......... "
        f"{result.rule_counts[RULE_CLOSED_NO_SCORE]}"
    )
    print(
        f"  └─ Score out of range ............ "
        f"{result.rule_counts[RULE_SCORE_OUT_OF_RANGE]}"
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
        print(
            f"  {branch} {label} {count}  ({_pct_label(count, valid_count)})"
        )
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
        print(
            f"  {branch} {label} {count}  ({_pct_label(count, valid_count)})"
        )
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


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python analyze.py <path-to-incidents.csv>", file=sys.stderr)
        return 1

    csv_path = Path(args[0])
    if not csv_path.is_file():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        return 1

    result = analyze_path(csv_path)
    print_report(result)

    try:
        answer = input("Export results to CSV? [y / n]: ").strip().lower()
    except EOFError:
        answer = "n"

    if answer == "y":
        output_path = Path("results.csv")
        output_path.write_text(export_results_csv_text(result), encoding="utf-8")
        print(f"Saved {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
