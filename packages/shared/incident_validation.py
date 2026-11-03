"""CSV rules from the incident analyzer, plus the manager vocabulary.

The seed script and the API both import this module. Do not copy the rules.
"""

from __future__ import annotations

from datetime import datetime, timezone

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

MANAGER_STATUSES = ("open", "in_progress", "resolved", "discarded")
MANAGER_ORIGINS = ("customer", "branch", "internal")
MANAGER_CATEGORIES = (
    "equipment_failure",
    "supply_issue",
    "customer_complaint",
    "staff_issue",
    "facility_issue",
    "pos_system",
    "delivery_issue",
    "other",
)
MANAGER_BRANCHES = (
    ("central", "Central (Medellín / Miami)"),
    ("medellin_centro", "Medellín Centro"),
    ("medellin_laureles", "Medellín Laureles"),
    ("medellin_envigado", "Medellín Envigado"),
    ("medellin_bello", "Medellín Bello"),
    ("medellin_itagui", "Medellín Itagüí"),
    ("bogota_chapinero", "Bogotá Chapinero"),
    ("bogota_usaquen", "Bogotá Usaquén"),
    ("cali_granada", "Cali Granada"),
    ("barranquilla_norte", "Barranquilla Norte"),
    ("miami_doral", "Miami Doral"),
    ("miami_hialeah", "Miami Hialeah"),
    ("miami_kendall", "Miami Kendall"),
    ("orlando_international", "Orlando International Drive"),
    ("fort_lauderdale", "Fort Lauderdale"),
)
BRANCH_VALUES = tuple(value for value, _label in MANAGER_BRANCHES)
BRANCH_LABELS = dict(MANAGER_BRANCHES)

CSV_STATUS_MAP = {
    "OPEN": "open",
    "CLOSED": "resolved",
    "DISCARDED": "discarded",
}
CSV_CATEGORY_MAP = {
    "CUSTOMER_COMPLAINT": "customer_complaint",
    "EQUIPMENT": "equipment_failure",
    "SUPPLY": "supply_issue",
    "FOOD_QUALITY": "customer_complaint",
    "STAFF": "staff_issue",
}
CSV_BRANCH_MAP = {
    "COL-01": "medellin_centro",
    "COL-02": "medellin_laureles",
    "COL-03": "medellin_envigado",
    "COL-04": "medellin_bello",
    "COL-05": "medellin_itagui",
    "COL-06": "bogota_chapinero",
    "COL-07": "bogota_usaquen",
    "COL-08": "cali_granada",
    "COL-09": "barranquilla_norte",
    "COL-10": "central",
    "FLA-01": "miami_doral",
    "FLA-02": "miami_hialeah",
    "FLA-03": "miami_kendall",
    "FLA-04": "orlando_international",
}

TRANSITIONS = {
    "open": frozenset({"in_progress", "discarded"}),
    "in_progress": frozenset({"resolved", "discarded"}),
    "resolved": frozenset(),
    "discarded": frozenset(),
}

FIELD_MESSAGES = {
    "title": "Enter a short title.",
    "description": "Enter a description.",
    "category": "Choose a category from the list.",
    "status": "Choose a valid status.",
    "origin": "Choose where this report came from.",
    "branch": "Choose a branch.",
}


def cell(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def parse_score(raw: str) -> int | None | str:
    value = raw.strip()
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return "invalid"


def classify_row(row: dict[str, str]) -> list[str]:
    """Return the analyzer rule names that make this CSV row invalid."""
    reasons: list[str] = []

    location_id = cell(row, "location_id")
    if not location_id or location_id not in VALID_LOCATIONS:
        reasons.append(RULE_MISSING_LOCATION)

    category = cell(row, "category")
    if not category or category not in VALID_CATEGORIES:
        reasons.append(RULE_INVALID_CATEGORY)

    description = cell(row, "description")
    if len(description) < 5:
        reasons.append(RULE_EMPTY_DESCRIPTION)

    reporter_id = cell(row, "reporter_id")
    if not reporter_id:
        reasons.append(RULE_MISSING_REPORTER)

    status = cell(row, "status")
    score = parse_score(cell(row, "satisfaction_score"))

    if status == "CLOSED" and score is None:
        reasons.append(RULE_CLOSED_NO_SCORE)

    if score == "invalid" or (isinstance(score, int) and not 1 <= score <= 5):
        reasons.append(RULE_SCORE_OUT_OF_RANGE)

    return reasons


def seed_record(row: dict[str, str]) -> tuple[dict | None, str | None]:
    """Turn one analyzer row into a manager incident, or a console reason."""
    reasons = classify_row(row)
    if reasons:
        return None, ", ".join(reasons)

    description = cell(row, "description")
    title = description[:120].strip()
    if not title:
        return None, "empty title after trim"

    try:
        created_at = datetime.strptime(cell(row, "date"), "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None, "date is not YYYY-MM-DD"

    csv_status = cell(row, "status")
    status = CSV_STATUS_MAP.get(csv_status)
    if status is None:
        return None, f"unmapped status {csv_status or '(blank)'}"

    csv_category = cell(row, "category")
    category = CSV_CATEGORY_MAP.get(csv_category)
    if category is None:
        return None, f"unmapped category {csv_category or '(blank)'}"

    branch = CSV_BRANCH_MAP.get(cell(row, "location_id"), "central")
    seed_key = cell(row, "incident_id") or cell(row, "ticket_id")
    if not seed_key:
        seed_key = f"{title}|{created_at.isoformat()}"

    return (
        {
            "title": title,
            "description": description,
            "category": category,
            "status": status,
            "origin": "customer",
            "branch": branch,
            "created_at": created_at,
            "updated_at": created_at,
            "seed_key": seed_key,
        },
        None,
    )


def field_error(payload: dict, key: str, allowed: tuple[str, ...] | None = None) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        return FIELD_MESSAGES[key]
    if allowed is not None and value.strip() not in allowed:
        return FIELD_MESSAGES[key]
    return None


def validate_incident_fields(payload: dict) -> tuple[str, str] | None:
    """First invalid field on a new incident, as (field, plain message)."""
    checks = (
        ("title", None),
        ("description", None),
        ("category", MANAGER_CATEGORIES),
        ("status", MANAGER_STATUSES),
        ("origin", MANAGER_ORIGINS),
        ("branch", BRANCH_VALUES),
    )
    for key, allowed in checks:
        message = field_error(payload, key, allowed)
        if message:
            return key, message
    return None


def transition_error(current: str, nxt: str) -> str | None:
    if nxt not in MANAGER_STATUSES:
        return FIELD_MESSAGES["status"]
    if nxt not in TRANSITIONS.get(current, frozenset()):
        return "That status change is not allowed."
    return None
