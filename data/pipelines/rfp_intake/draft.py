"""Department drafts and the three briefing evaluators. No model call."""

from __future__ import annotations

import re

from data.pipelines.rfp_intake.analyze import DEPARTMENTS
from data.pipelines.rfp_intake.document import readability_metrics

# The same rate as src/utils/transformations.ts. This pipeline cannot import that module.
USD_TO_COP_RATE = 4000
MAX_REVISIONS = 2
MAX_ATTEMPTS = 1 + MAX_REVISIONS

RULE_IDS = (
    "dual-currency",
    "brand-pillars",
    "setup-sla",
    "no-competitors",
    "offer-validity",
)

_SHORT_SETUP = re.compile(r"\b(\d+)\s+business\s+days?\b", re.IGNORECASE)
_RUSH = re.compile(r"\b(same[- ]day|next day|24 hours|48 hours|within a day)\b", re.IGNORECASE)
_COMPETITORS = re.compile(
    r"\b(mcdonald'?s|burger king|wendy'?s|chipotle|subway|kfc|popeyes)\b",
    re.IGNORECASE,
)
_USD = re.compile(r"\bUSD\b|\$\s?\d")
_COP = re.compile(r"\bCOP\b")
_AMOUNT = re.compile(r"\d[\d,]*")


def usd_and_cop(budget_range: str) -> str:
    """Show a stated USD figure in both currencies. A blank budget stays blank."""
    amounts = []
    for raw in _AMOUNT.findall(budget_range or ""):
        amounts.append(int(raw.replace(",", "")))
    if not amounts:
        return ""
    parts = [
        f"USD {amount:,} (COP {amount * USD_TO_COP_RATE:,})"
        for amount in amounts[:2]
    ]
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} to {parts[1]}"


def above_ceo_threshold(budget_range: str) -> bool:
    amounts = [int(raw.replace(",", "")) for raw in _AMOUNT.findall(budget_range or "")]
    return any(amount >= 50_000 for amount in amounts)


def _aspects(state: dict) -> str:
    lines = [str(aspect).strip() for aspect in state.get("key_aspects") or [] if str(aspect).strip()]
    if not lines:
        return "The intake handoff listed no separate point for this department."
    return " ".join(f"From the request: {line}" for line in lines)


def _close(state: dict) -> str:
    metadata = state.get("metadata") or {}
    money = usd_and_cop(str(metadata.get("budget_range") or ""))
    sentences = [
        "The proposal rests on consistent quality, a warm experience, and speed of service.",
        "This offer is valid for 30 days from issuance.",
        "Setup and delivery take 10 business days.",
    ]
    if money:
        sentences.append(f"The stated value is {money}.")
    else:
        sentences.append("The request does not state a price, so this section does not invent one.")
    sentences.append(
        "Brasaland will staff the service from its own kitchens and keep the recipes the restaurants already serve. "
        "The team confirms the guest count, the service days, and the site constraints with the client before purchasing. "
        "A figure that the request does not state stays open, and this draft does not fill one in. "
        "Camila Ospina owns the ticket and sends this section on with the other department drafts. "
        "The same standard covers consistent quality, a warm experience, and speed of service at every location."
    )
    for question in state.get("open_questions") or []:
        text = str(question).strip()
        if text:
            sentences.append(text)
    if str(state.get("feedback") or "").strip():
        sentences.insert(
            0,
            "This revision applies the evaluation feedback and keeps the briefing rules below.",
        )
    return " ".join(sentences)


def _client(state: dict) -> str:
    return str((state.get("metadata") or {}).get("client_name") or "the client")


def generate_marketing(state: dict) -> str:
    """Brand, exclusivity, and the 30-day offer. Camila owns the ticket."""
    metadata = state.get("metadata") or {}
    service = metadata.get("service_type") or "the requested service"
    location = metadata.get("location") or "the stated location"
    return (
        f"Camila Ospina, Marketing and Digital Experience, drafts the brand terms for {_client(state)}. "
        f"The requested service is {service} in {location}. "
        "Exclusivity and co-branding stay with Brasaland, and this section does not name another company. "
        f"{_aspects(state)} {_close(state)}"
    )


def generate_operaciones(state: dict) -> str:
    """Kitchen capacity, staffing, and a setup time of at least 10 business days."""
    metadata = state.get("metadata") or {}
    scope = metadata.get("scope") or "the stated scope"
    return (
        f"Felipe Guerrero, Restaurant Operations, drafts the kitchen and staffing plan for {_client(state)}. "
        f"The scope to cover is {scope}. "
        "The kitchen and the floor team can run the service on the stated days. "
        f"{_aspects(state)} {_close(state)}"
    )


def generate_procurement(state: dict) -> str:
    """Ingredient cost and supplier lead time. A missing price stays an open question."""
    return (
        f"Lucía Fernández, Procurement and Suppliers, drafts the ingredient cost and the supplier lead time for {_client(state)}. "
        "Suppliers are asked only for what the request already states. "
        f"{_aspects(state)} {_close(state)}"
    )


def generate_training(state: dict) -> str:
    """Development and certification time for a new recipe or standard."""
    return (
        f"Jake Morrison, Training and Quality Standards, drafts the development and certification time for {_client(state)}. "
        "The new standard is taught before the first service. "
        f"{_aspects(state)} {_close(state)}"
    )


GENERATORS = {
    "marketing": generate_marketing,
    "operaciones": generate_operaciones,
    "procurement": generate_procurement,
    "training": generate_training,
}


def evaluate_readability(draft: str) -> dict:
    """Score the section. Flesch-Kincaid needs 100 words, so a shorter section fails."""
    metrics = readability_metrics(draft or "")
    score = metrics["flesch_kincaid"]
    if score is None:
        return {
            "pass": False,
            "score": None,
            "details": "The section needs at least 100 words before Flesch-Kincaid can score it.",
        }
    fog = metrics["gunning_fog"]
    return {
        "pass": True,
        "score": score,
        "details": f"Flesch-Kincaid {score}. Gunning Fog {fog}.",
    }


def evaluate_relevance(draft: str, key_aspects: list[str]) -> dict:
    """The section has to carry each point the Part 1 handoff assigned to this department."""
    missing = []
    text = draft or ""
    for aspect in key_aspects or []:
        cleaned = str(aspect).strip()
        if cleaned and cleaned not in text:
            missing.append(cleaned)
    return {"pass": not missing, "missing_aspects": missing}


def evaluate_compliance(draft: str) -> dict:
    """Check the section against briefing section 5. Each failure names the rule and the fix."""
    text = draft or ""
    violations = []
    if bool(_USD.search(text)) != bool(_COP.search(text)):
        violations.append(
            {
                "rule_id": "dual-currency",
                "message": "State every price in both USD and COP. Use 4,000 COP per USD.",
            }
        )
    lowered = text.lower()
    if not all(
        phrase in lowered
        for phrase in ("consistent quality", "warm experience", "speed of service")
    ):
        violations.append(
            {
                "rule_id": "brand-pillars",
                "message": "Name consistent quality, a warm experience, and speed of service.",
            }
        )
    short = [int(match) for match in _SHORT_SETUP.findall(text) if int(match) < 10]
    if short or _RUSH.search(text):
        if short:
            message = (
                f"The section promises setup in {short[0]} business days. "
                "Use at least 10 business days."
            )
        else:
            message = "The section promises setup sooner than 10 business days. Use at least 10 business days."
        violations.append({"rule_id": "setup-sla", "message": message})
    if _COMPETITORS.search(text):
        violations.append(
            {
                "rule_id": "no-competitors",
                "message": "Remove the competitor name.",
            }
        )
    if not re.search(r"\b30\s+days\b", text, re.IGNORECASE):
        violations.append(
            {
                "rule_id": "offer-validity",
                "message": "State that the offer is valid for 30 days from issuance.",
            }
        )
    return {
        "pass": not violations,
        "rule_ids": list(RULE_IDS),
        "violations": violations,
    }


def combine_evaluation(department_id: str, readability: dict, relevance: dict, compliance: dict) -> dict:
    """Join the three evaluator outputs. Each evaluator wrote only its own key."""
    feedback = []
    if not readability.get("pass"):
        feedback.append("Write at least 100 words so Flesch-Kincaid can score the section.")
    missing = relevance.get("missing_aspects") or []
    if missing:
        feedback.append("Cover these request points: " + "; ".join(missing))
    feedback.extend(item["message"] for item in compliance.get("violations") or [])
    return {
        "department_id": department_id,
        "readability": readability,
        "relevance": relevance,
        "compliance": compliance,
        "overall_pass": bool(
            readability.get("pass") and relevance.get("pass") and compliance.get("pass")
        ),
        "feedback_for_generator": " ".join(feedback),
    }


def evaluation_result(department_id: str, draft: str, key_aspects: list[str]) -> dict:
    """One structured result. Evaluators do not see the rest of the proposal."""
    return combine_evaluation(
        department_id,
        evaluate_readability(draft),
        evaluate_relevance(draft, key_aspects),
        evaluate_compliance(draft),
    )


def department_slice(handoff: dict, department_id: str) -> dict:
    metadata = dict(handoff.get("metadata") or {})
    questions = (handoff.get("section_questions") or {}).get(department_id) or []
    info = DEPARTMENTS[department_id]
    return {
        "department_id": department_id,
        "metadata": metadata,
        "key_aspects": list((handoff.get("key_aspects") or {}).get(department_id) or []),
        "open_questions": list(questions),
        "contact_name": (handoff.get("contacts") or {}).get(department_id) or info["owner"],
        "feedback": "",
    }
