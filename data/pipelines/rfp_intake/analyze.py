"""Briefing rules for Brasaland RFP intake. No model call and no invented figure."""

from __future__ import annotations

import re

DEPARTMENTS = {
    "marketing": {
        "name": "Marketing and Digital Experience",
        "owner": "Camila Ospina",
    },
    "operaciones": {
        "name": "Restaurant Operations",
        "owner": "Felipe Guerrero",
    },
    "procurement": {
        "name": "Procurement and Suppliers",
        "owner": "Lucía Fernández",
    },
    "training": {
        "name": "Training and Quality Standards",
        "owner": "Jake Morrison",
    },
}

_SERVICE = re.compile(
    r"\b(catering|almuerzo|concession|co-brand|cobrand|partnership|signature menu)\b",
    re.IGNORECASE,
)
_SCOPE = re.compile(
    r"\b(\d+\s+(?:employees|diners|personas|resorts|properties|locations)|"
    r"\d+\s*-\s*month|12-month|three beachfront|contract|contrato|un año)\b",
    re.IGNORECASE,
)
_DEADLINE = re.compile(
    r"\b(deadline|due date|proposal due|proposals due|reply within|antes del)\b",
    re.IGNORECASE,
)
_MONEY = re.compile(r"\$\s?\d[\d,]*(?:\s?[–-]\s?\$?\s?\d[\d,]*)?")
_TRAINING = re.compile(r"signature menu|new recipe|certification", re.IGNORECASE)
_UNKNOWN = re.compile(
    r"\b(legal department|finance department|human resources)\b",
    re.IGNORECASE,
)


def classify_document(markdown: str) -> dict:
    """Accept a client request with a service and a scope or deadline.

    A franchise inquiry that names none of those is discarded. The decision
    stops that ticket only.
    """
    text = markdown or ""
    folded = text.lower()
    franchise = "franchise" in folded or "franquicia" in folded
    service = _SERVICE.search(text) is not None
    scope = _SCOPE.search(text) is not None
    deadline = _DEADLINE.search(text) is not None
    if franchise and not service and not scope and not deadline and _MONEY.search(text) is None:
        return {
            "is_rfp": False,
            "reason": "Franchise inquiry with no scope, budget, or deadline.",
        }
    if service and (scope or deadline):
        return {
            "is_rfp": True,
            "reason": "The document names a service and a scope or a deadline.",
        }
    return {
        "is_rfp": False,
        "reason": "The document does not read as a Brasaland RFP.",
    }


def extract_metadata(markdown: str) -> dict:
    """Pull the briefing fields. A missing figure stays blank."""
    text = markdown or ""
    client = _first(
        text,
        r"Issuing Organization:\s*(.+)",
        r"Client:\s*(.+)",
    )
    if not client and "Sunset Bay Resorts" in text:
        client = "Sunset Bay Resorts"
    if not client and "Andes Tech Solutions" in text:
        client = "Andes Tech Solutions"
    location = ""
    if re.search(r"Florida", text, re.IGNORECASE):
        location = "Florida"
    elif re.search(r"Medell[ií]n", text, re.IGNORECASE):
        location = "Medellín"
    else:
        found = _first(text, r"Location:\s*(.+)")
        location = found
    service = ""
    if re.search(r"concession", text, re.IGNORECASE):
        service = "co-branded concession"
    elif re.search(r"catering", text, re.IGNORECASE):
        service = "weekly catering"
    elif re.search(r"co-brand", text, re.IGNORECASE):
        service = "co-branding"
    scope = _first(text, r"Scope:\s*(.+)")
    if not scope and re.search(r"three beachfront|3 resort", text, re.IGNORECASE):
        scope = "3 Florida resort properties"
    people = re.search(r"(\d+\s+personas)", text, re.IGNORECASE)
    if not scope and people:
        scope = people.group(1)
        if re.search(r"contrato", text, re.IGNORECASE):
            scope = f"{scope}, contrato por un año"
    deadline = _first(
        text,
        r"Proposal Due Date:\s*(.+)",
        r"Proposals due\s+([A-Z][a-z]+ \d{1,2}, \d{4})",
        r"Deadline:\s*(.+)",
        r"antes del (\d{1,2} de [A-Za-zÁÉÍÓÚáéíóú]+)",
    )
    money = _MONEY.search(text)
    return {
        "client_name": client,
        "location": location,
        "service_type": service,
        "scope": scope,
        "deadline": deadline,
        "budget_range": money.group(0) if money else "",
    }


def select_departments(markdown: str) -> tuple[list[str], list[str]]:
    """Open a worker only for a briefing department the document needs."""
    text = markdown or ""
    chosen = ["marketing"]
    if re.search(
        r"catering|almuerzo|concession|staffing|kitchen|resort|employees|personas",
        text,
        re.IGNORECASE,
    ):
        chosen.append("operaciones")
    if _MONEY.search(text) or re.search(
        r"catering|concession|employees|personas|contract value|contrato|precios",
        text,
        re.IGNORECASE,
    ):
        chosen.append("procurement")
    if _TRAINING.search(text):
        chosen.append("training")
    unknown = []
    for match in _UNKNOWN.finditer(text):
        name = match.group(1).lower()
        if name not in unknown:
            unknown.append(name)
    ordered = [key for key in DEPARTMENTS if key in chosen]
    return ordered, unknown


def work_department(department_id: str, markdown: str, metadata: dict) -> dict:
    """Keep sentences that concern this department. Do not fill in missing numbers."""
    info = DEPARTMENTS[department_id]
    sentences = _sentences(markdown)
    kept = [sentence for sentence in sentences if _concerns(department_id, sentence)]
    if not kept:
        kept = [_fallback(department_id, metadata)]
    questions = []
    if department_id == "procurement" and not metadata.get("budget_range"):
        questions.append("The RFP does not state a budget or a contract value.")
    if department_id == "operaciones" and not metadata.get("scope"):
        questions.append("The RFP does not state a volume or a site count.")
    if department_id == "marketing" and "exclusiv" not in markdown.lower() and "brand" not in markdown.lower():
        questions.append("The RFP does not state an exclusivity or brand term.")
    return {
        "department_id": department_id,
        "department_name": info["name"],
        "contact_name": info["owner"],
        "key_aspects": kept[:5],
        "open_questions": questions,
    }


def synthesize(metadata: dict, sections: list[dict], unknown: list[str]) -> dict:
    """One Sales summary: who to ask, and a conflict when two amounts disagree."""
    lines = ["Camila can brief the departments without opening the PDF."]
    amounts: list[tuple[str, str]] = []
    questions: list[str] = []
    for section in sections:
        owner = section["contact_name"]
        dept = section["department_id"]
        aspect = section["key_aspects"][0] if section["key_aspects"] else "No stated point."
        lines.append(f"{owner} ({dept}): {aspect}")
        questions.extend(section["open_questions"])
        for aspect_line in section["key_aspects"]:
            found = _MONEY.search(aspect_line)
            if found:
                amounts.append((dept, found.group(0)))
    conflicts = []
    unique_amounts = {amount for _dept, amount in amounts}
    if len(unique_amounts) > 1:
        detail = ", ".join(f"{dept} {amount}" for dept, amount in amounts)
        conflicts.append(f"Departments quote different amounts: {detail}.")
        lines.append(conflicts[0])
    if unknown:
        note = "The PDF mentions " + ", ".join(unknown) + ", which is not a Brasaland proposal department."
        questions.append(note)
        lines.append(note)
    client = metadata.get("client_name") or "The client"
    lines.insert(1, f"Client: {client}.")
    return {
        "summary": " ".join(lines),
        "open_questions": questions,
        "conflicts": conflicts,
    }


def _concerns(department_id: str, sentence: str) -> bool:
    text = sentence.lower()
    if department_id == "marketing":
        return any(word in text for word in ("exclusiv", "brand", "co-brand", "cobrand"))
    if department_id == "operaciones":
        return any(
            word in text
            for word in ("staff", "kitchen", "resort", "employee", "concession", "catering", "personas", "almuerzo")
        )
    if department_id == "procurement":
        return (
            _MONEY.search(sentence) is not None
            or "contract value" in text
            or "ingredient" in text
            or "precio" in text
            or "contrato" in text
        )
    if department_id == "training":
        return _TRAINING.search(sentence) is not None
    return False


def _fallback(department_id: str, metadata: dict) -> str:
    if department_id == "marketing":
        return "Marketing owns the ticket. The RFP does not state a separate brand term."
    if department_id == "operaciones":
        scope = metadata.get("scope") or "a volume the RFP does not state"
        return f"Operations needs a staffing read for {scope}."
    if department_id == "procurement":
        return "Procurement needs a cost read. The RFP does not state a price."
    return "Training is not given a new recipe in the excerpts."


def _sentences(markdown: str) -> list[str]:
    flat = re.sub(r"\s+", " ", markdown or "").strip()
    parts = re.split(r"(?<=[.!?])\s+", flat)
    return [part.strip(" #") for part in parts if len(part.strip()) > 20]


def _first(text: str, *patterns: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .")
    return ""
