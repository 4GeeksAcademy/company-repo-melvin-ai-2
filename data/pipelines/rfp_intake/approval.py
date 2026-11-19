"""Human approval rules for an RFP. No model call and no invented price."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from data.pipelines.rfp_intake.analyze import DEPARTMENTS
from data.pipelines.rfp_intake.draft import USD_TO_COP_RATE, above_ceo_threshold, usd_and_cop

DECISIONS = ("approve", "reject", "request_changes")
MAX_ARBITRATION_ROUNDS = 2
MAX_CHANGE_ROUNDS = 2
CEO_ID = "ceo"
CEO_OWNER = "Mariana Restrepo"

_SHORT_SETUP = re.compile(r"\b(\d+)\s+business\s+days?\b", re.IGNORECASE)
_USD = re.compile(r"USD\s+([\d,]+)(?:\s+\(COP\s+[\d,]+\))?")


def thread_id(ticket_id: str, department_id: str) -> str:
    """One checkpoint per ticket and department. Two tickets never share a thread."""
    return f"rfp-{ticket_id}:{department_id}"


def validate_decision(decision: str) -> str:
    cleaned = (decision or "").strip().lower()
    if cleaned not in DECISIONS:
        raise ValueError("The decision must be approve, reject, or request changes.")
    return cleaned


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_step(trace: list | None, agent: str, step_input: dict, step_output: dict) -> list:
    """Append one node execution. The fields are the agent, its input, its output, and the time."""
    entries = list(trace or [])
    entries.append(
        {
            "agent": agent,
            "input": step_input,
            "output": step_output,
            "timestamp": _now(),
        }
    )
    return entries


def _amounts(text: str) -> list[int]:
    found = []
    for raw in _USD.findall(text or ""):
        found.append(int(raw.replace(",", "")))
    return found


def detect_conflicts(sections: list[dict], metadata: dict, ceo_approved: bool = False) -> list[dict]:
    """Read structured amounts and setup days. The node does not vote in prose."""
    by_id = {section["department_id"]: section for section in sections}
    conflicts = []
    offenders = []
    for section in sections:
        if section["department_id"] == CEO_ID:
            continue
        days = [int(match) for match in _SHORT_SETUP.findall(section.get("draft_content") or "") if int(match) < 10]
        if days:
            offenders.append(section["department_id"])
    if offenders:
        conflicts.append(
            {
                "trigger_id": "setup-sla-breach",
                "arbiter": "Felipe Guerrero",
                "escalation": "Camila Ospina" if offenders != ["operaciones"] else "",
                "department_ids": offenders,
            }
        )
    operaciones = _amounts((by_id.get("operaciones") or {}).get("draft_content") or "")
    procurement = _amounts((by_id.get("procurement") or {}).get("draft_content") or "")
    if operaciones and procurement and max(procurement) > max(operaciones):
        conflicts.append(
            {
                "trigger_id": "cost-vs-feasibility",
                "arbiter": "Camila Ospina",
                "department_ids": ["operaciones", "procurement"],
                "operaciones_usd": max(operaciones),
                "procurement_usd": max(procurement),
            }
        )
    budget = str((metadata or {}).get("budget_range") or "")
    if above_ceo_threshold(budget) and not ceo_approved:
        conflicts.append(
            {
                "trigger_id": "ceo-threshold",
                "arbiter": CEO_OWNER,
                "department_ids": [CEO_ID],
            }
        )
    return conflicts


def _raise_setup(text: str) -> str:
    def replace(match: re.Match) -> str:
        if int(match.group(1)) < 10:
            return "10 business days"
        return match.group(0)

    return _SHORT_SETUP.sub(replace, text or "")


def _raise_price(text: str, target_usd: int) -> str:
    cop = target_usd * USD_TO_COP_RATE
    replacement = f"USD {target_usd:,} (COP {cop:,})"
    updated, count = _USD.subn(replacement, text or "", count=1)
    if count:
        return updated
    return f"{text} The price is now {replacement}."


def apply_arbitration(conflicts: list[dict], sections: list[dict]) -> tuple[list[dict], list[dict]]:
    """The briefing names the arbiter. The rule rewrites the structured breach."""
    updated = [dict(section) for section in sections]
    by_id = {section["department_id"]: section for section in updated}
    applied = []
    for conflict in conflicts:
        trigger = conflict["trigger_id"]
        if trigger == "setup-sla-breach":
            for department_id in conflict["department_ids"]:
                section = by_id.get(department_id)
                if section:
                    section["draft_content"] = _raise_setup(section.get("draft_content") or "")
            applied.append(
                {
                    **conflict,
                    "action": "request_changes",
                    "detail": "Felipe Guerrero set setup and delivery to 10 business days.",
                }
            )
        elif trigger == "cost-vs-feasibility":
            target = int(conflict["procurement_usd"])
            section = by_id.get("operaciones")
            if section:
                section["draft_content"] = _raise_price(section.get("draft_content") or "", target)
            applied.append(
                {
                    **conflict,
                    "action": "request_changes",
                    "detail": (
                        f"Camila Ospina raised the operaciones price to USD {target:,} "
                        f"(COP {target * USD_TO_COP_RATE:,})."
                    ),
                }
            )
        elif trigger == "ceo-threshold":
            applied.append(
                {
                    **conflict,
                    "action": "block_synthesis",
                    "detail": "Mariana Restrepo must approve before the final document is written.",
                }
            )
    return updated, applied


def _actionable(conflicts: list[dict]) -> list[dict]:
    return [conflict for conflict in conflicts if conflict["trigger_id"] != "ceo-threshold"]


def run_arbitration_rounds(
    sections: list[dict],
    metadata: dict,
    ceo_approved: bool = False,
    apply=None,
) -> dict:
    """Stop after two rounds even when a breach is still present."""
    rule = apply_arbitration if apply is None else apply
    current = [dict(section) for section in sections]
    conflicts = detect_conflicts(current, metadata, ceo_approved)
    applied: list[dict] = []
    trace: list[dict] = []
    rounds = 0
    while _actionable(conflicts) and rounds < MAX_ARBITRATION_ROUNDS:
        rounds += 1
        step_input = {"conflicts": conflicts, "round": rounds}
        current, step_applied = rule(conflicts, current)
        applied.extend(step_applied)
        conflicts = detect_conflicts(current, metadata, ceo_approved)
        trace = log_step(
            trace,
            "arbitrate",
            step_input,
            {"applied": step_applied, "remaining": conflicts},
        )
    if not trace:
        trace = log_step(
            trace,
            "arbitrate",
            {"conflicts": conflicts, "round": 0},
            {"applied": [], "remaining": conflicts},
        )
    return {
        "sections": current,
        "conflicts": conflicts,
        "rounds": rounds,
        "applied": applied,
        "trace": trace,
    }


def offer_for_section(section: dict) -> dict:
    """The signer sees this section only, not the whole PDF."""
    evaluation = section.get("evaluation") or {}
    return {
        "department_id": section["department_id"],
        "owner": section.get("owner") or section.get("contact_name") or "",
        "draft_content": section.get("draft_content") or "",
        "evaluation_passed": evaluation.get("overall_pass"),
        "feedback_for_generator": evaluation.get("feedback_for_generator") or "",
        "open_questions": list(section.get("open_questions") or []),
    }


def apply_human_decision(state: dict, decision: str) -> dict:
    """Record the sign-off. A rejection does not start another draft."""
    owner = state.get("owner") or ""
    rounds = int(state.get("approval_rounds") or 0)
    result = {
        "decision": decision,
        "approver": "",
        "approved_at": "",
        "approval_rounds": rounds,
        "limit_reached": False,
    }
    if decision == "approve":
        result["approval_status"] = "approved"
        result["approver"] = owner
        result["approved_at"] = _now()
    elif decision == "reject":
        result["approval_status"] = "rejected"
        result["approver"] = owner
        result["approved_at"] = _now()
    else:
        rounds += 1
        result["approval_rounds"] = rounds
        if rounds >= MAX_CHANGE_ROUNDS:
            result["approval_status"] = "request_changes"
            result["limit_reached"] = True
        else:
            result["approval_status"] = "pending"
    return result


def ceo_required(metadata: dict, ceo_approved: bool = False) -> bool:
    return above_ceo_threshold(str((metadata or {}).get("budget_range") or "")) and not ceo_approved


def ceo_section(metadata: dict) -> dict:
    money = usd_and_cop(str((metadata or {}).get("budget_range") or ""))
    stated = money or "the stated contract value"
    return {
        "department_id": CEO_ID,
        "owner": CEO_OWNER,
        "contact_name": CEO_OWNER,
        "draft_content": (
            f"The estimated contract is {stated}. "
            "Mariana Restrepo must approve before Brasaland sends the final proposal."
        ),
        "evaluation": {},
        "open_questions": [],
        "approval_status": "pending",
    }


def ready_for_document(sections: list[dict], metadata: dict) -> bool:
    departments = [section for section in sections if section["department_id"] != CEO_ID]
    if not departments or any(section.get("approval_status") != "approved" for section in departments):
        return False
    ceo = next((section for section in sections if section["department_id"] == CEO_ID), None)
    ceo_approved = bool(ceo and ceo.get("approval_status") == "approved")
    if above_ceo_threshold(str((metadata or {}).get("budget_range") or "")) and not ceo_approved:
        return False
    remaining = _actionable(detect_conflicts(sections, metadata, ceo_approved))
    return not remaining


def render_final_document(client_name: str, sections: list[dict], metadata: dict, generated_at: str) -> str:
    """One proposal from the approved sections. Unapproved sections are left out."""
    lines = [
        f"# Brasaland proposal for {client_name or 'the client'}",
        "",
        "This offer is valid for 30 days from issuance.",
        "Setup and delivery take 10 business days.",
        "The proposal rests on consistent quality, a warm experience, and speed of service.",
        "",
    ]
    money = usd_and_cop(str((metadata or {}).get("budget_range") or ""))
    if money:
        lines.append(f"Total estimated value: {money}.")
    else:
        lines.append("Total estimated value: not stated in the request.")
    lines.append("")
    for section in sections:
        if section["department_id"] == CEO_ID or section.get("approval_status") != "approved":
            continue
        owner = section.get("approver") or section.get("owner") or section.get("contact_name") or ""
        title = DEPARTMENTS.get(section["department_id"], {}).get("name") or section["department_id"]
        lines.append(f"## {title}")
        lines.append(f"{owner} approved this section.")
        lines.append(section.get("draft_content") or "")
        lines.append("")
    if any(section["department_id"] == CEO_ID and section.get("approval_status") == "approved" for section in sections):
        lines.append(f"{CEO_OWNER} approved the contract before this document was written.")
    lines.append(f"Generated at {generated_at}.")
    return "\n".join(lines).strip() + "\n"
