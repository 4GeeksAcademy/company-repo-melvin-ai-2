"""Episodic memory for the support agent.

Approved corrections live in a key-value store named for the agent. They never
enter the Qdrant collection `brasaland_knowledge`. The graph calls `read_memory`
and `write_memory`. It does not append the chat to the prompt.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "data" / "agent_memory" / "brasaland_agent_memory.sqlite"
MEMORY_CAP = 20
SILENCE_SECONDS = 15 * 60

PROPOSAL_QUESTION = "Want me to remember this for next time?"
FORBIDDEN_REPLY = "I can't remember that. The briefing forbids it."
APPROVED_REPLY = "I'll remember that."
REJECTED_REPLY = "I won't remember that."
EDITED_REPLY = "I'll remember the edited version."


class MemoryRefusal(Exception):
    """The briefing forbids this fact, so it was not stored."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(text: str) -> str:
    folded = text.lower()
    for src, dst in (("é", "e"), ("í", "i"), ("á", "a"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        folded = folded.replace(src, dst)
    return re.sub(r"\s+", " ", folded).strip(" .")


def fact_key(fact: str) -> str:
    return _norm(fact)


def forbidden_reason(fact: str) -> str | None:
    """Restrictions from the Brasaland RAG and incident briefings.

    The manuals own official numbers. Allergen answers cannot become "zero risk".
    Currency is not converted. Customer contact data, passwords, and secrets stay out.
    """
    text = _norm(fact)
    if "zero risk" in text or re.search(r"\bno allergen\b|\brisk-free\b|\bsafe for everyone\b", text):
        return "Allergen answers cannot be stored as zero risk."
    if re.search(r"\b(password|token|secret|api key)\b", text):
        return "Passwords and secrets are not memory."
    if re.search(r"\b[\w.+-]+@[\w.-]+\.\w+\b", text):
        return "Email addresses are not memory."
    if re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", text):
        return "Phone numbers are not memory."
    currencies = ("usd", "cop", "dollar", "dollars", "peso", "pesos")
    if sum(1 for name in currencies if re.search(rf"\b{name}\b", text)) >= 2:
        return "Currency is not converted into memory."
    if re.search(r"\d+\s*%|\d+\s*points|\$\s*\d|\b\d+\s*(usd|cop|dollars|pesos|kg)\b", text):
        return "Manual numbers stay in the knowledge base."
    return None


def _as_proposal(fact: str, why: str) -> dict | None:
    cleaned = re.sub(r"\s+", " ", fact).strip(" .")
    if not cleaned:
        return None
    reason = forbidden_reason(cleaned)
    return {
        "fact": cleaned,
        "why": reason or why,
        "forbidden": reason is not None,
    }


def parse_structured_reply(raw: str) -> tuple[str, dict | None, bool]:
    """Split one model reply into the spoken answer and an optional proposal.

    Plain text has no proposal field. A JSON object from the same call carries
    `answer` and `memory_proposal`.
    """
    text = raw.strip()
    if not text.startswith("{"):
        return text, None, False
    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        return text, None, False
    if not isinstance(body, dict) or "answer" not in body:
        return text, None, False
    spoken = str(body.get("answer") or "").strip()
    proposal = body.get("memory_proposal")
    if not isinstance(proposal, dict):
        return spoken, None, True
    parsed = _as_proposal(
        str(proposal.get("fact") or ""),
        str(proposal.get("why") or "The reply contains a correction worth keeping."),
    )
    return spoken, parsed, True


def proposal_for(question: str, answer: str) -> dict | None:
    """Propose a correction the user stated, or one the reply named.

    A manual question, a greeting, and a tool lookup are not proposals.
    """
    structured_spoken, structured_proposal, was_structured = parse_structured_reply(answer)
    if was_structured:
        return structured_proposal
    text = question.strip()
    match = re.search(
        r"\b(?:remember that|remember this|from now on|correct the record:)\s*(.+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        match = re.match(
            r"(?:actually[,:\s]+|the correct (?:answer|record) is\s+)(.+)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
    if not match:
        return None
    del structured_spoken
    return _as_proposal(match.group(1), "The user stated an operational correction.")


def classify_decision(message: str) -> dict:
    """Label the next message against the pending proposal.

    The label is the whole decision act. A later question can follow that act.
    The word yes inside a new question is not approval.
    """
    text = message.strip()
    edit = re.match(
        r"^(?:edit|change it|change the memory|remember this instead)\s*:\s*(.+)$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if edit and edit.group(1).strip():
        return {"label": "edit", "remainder": "", "fact": edit.group(1).strip(" .")}

    pair = re.match(
        r"^(approve|approved|reject|rejected|yes|no|remember it|do not remember that|don't remember that)"
        r"[,.!]*\s*(.*)$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not pair:
        return {"label": "unclear", "remainder": text, "fact": ""}
    word = pair.group(1).lower()
    rest = pair.group(2).strip()
    label = "reject" if word in {"no", "reject", "rejected", "do not remember that", "don't remember that"} else "approve"
    if not rest or re.fullmatch(r"(remember it|please|thanks|thank you|that)", rest, flags=re.IGNORECASE):
        return {"label": label, "remainder": "", "fact": ""}
    if rest.endswith("?") or re.match(r"^(how|what|when|where|who|do|does|did|can|is|are)\b", rest, re.I):
        return {"label": label, "remainder": rest, "fact": ""}
    return {"label": "unclear", "remainder": text, "fact": ""}


class MemoryStore:
    """SQLite key-value memory. One pending proposal per thread."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path or DEFAULT_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT NOT NULL,
                fact TEXT NOT NULL,
                why TEXT NOT NULL,
                originating_message TEXT NOT NULL,
                approved_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pending (
                thread_id TEXT PRIMARY KEY,
                fact TEXT NOT NULL,
                why TEXT NOT NULL,
                originating_message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                proposal TEXT NOT NULL,
                decision TEXT NOT NULL,
                outcome TEXT NOT NULL,
                originating_message TEXT NOT NULL,
                decision_message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def read_memory(self) -> list[dict]:
        rows = self._db.execute(
            "SELECT fact, why, originating_message, approved_at FROM memories ORDER BY approved_at, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def relevant(self, question: str) -> list[dict]:
        haystack = _norm(question)
        found = []
        for row in self.read_memory():
            words = [word for word in re.findall(r"[a-z0-9]+", _norm(row["fact"])) if len(word) > 3]
            if any(word in haystack for word in words):
                found.append(row)
        return found

    def pending(self, thread_id: str) -> dict | None:
        row = self._db.execute(
            "SELECT fact, why, originating_message, created_at FROM pending WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
        return dict(row) if row else None

    def propose(self, thread_id: str, fact: str, why: str, originating_message: str) -> None:
        if self.pending(thread_id):
            raise RuntimeError("A proposal is already pending.")
        self._db.execute(
            """
            INSERT INTO pending (thread_id, fact, why, originating_message, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (thread_id, fact, why, originating_message, _now()),
        )
        self._db.commit()

    def write_memory(self, fact: str, *, why: str, originating_message: str, decision: str) -> dict:
        reason = forbidden_reason(fact)
        if reason:
            raise MemoryRefusal(reason)
        key = fact_key(fact)
        self._db.execute("DELETE FROM memories WHERE fact_key = ?", (key,))
        approved_at = _now()
        self._db.execute(
            """
            INSERT INTO memories (fact_key, fact, why, originating_message, approved_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, fact.strip(), why, originating_message, approved_at),
        )
        self._consolidate()
        self._db.commit()
        return {"fact": fact.strip(), "decision": decision, "approved_at": approved_at}

    def log(
        self,
        *,
        thread_id: str,
        proposal: str,
        decision: str,
        outcome: str,
        originating_message: str,
        decision_message: str,
    ) -> None:
        self._db.execute(
            """
            INSERT INTO audit (
                thread_id, proposal, decision, outcome, originating_message, decision_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                thread_id,
                proposal,
                decision,
                outcome,
                originating_message,
                decision_message,
                _now(),
            ),
        )
        self._db.commit()

    def audit(self) -> list[dict]:
        rows = self._db.execute(
            """
            SELECT thread_id, proposal, decision, outcome, originating_message, decision_message, created_at
            FROM audit ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def close_unanswered(self, *, max_age_seconds: float = SILENCE_SECONDS) -> int:
        """Reject pending proposals the user never answered. Nothing is stored."""
        now = datetime.now(timezone.utc)
        closed = 0
        rows = self._db.execute(
            "SELECT thread_id, fact, originating_message, created_at FROM pending"
        ).fetchall()
        for row in rows:
            created = datetime.fromisoformat(row["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if (now - created).total_seconds() < max_age_seconds:
                continue
            self.log(
                thread_id=row["thread_id"],
                proposal=row["fact"],
                decision="reject",
                outcome="discarded because the user did not answer",
                originating_message=row["originating_message"],
                decision_message="",
            )
            self.clear_pending(row["thread_id"])
            closed += 1
        return closed

    def clear_pending(self, thread_id: str) -> None:
        self._db.execute("DELETE FROM pending WHERE thread_id = ?", (thread_id,))
        self._db.commit()

    def _consolidate(self) -> None:
        """One row per fact, then the newest entries up to the cap."""
        self._db.execute(
            """
            DELETE FROM memories
            WHERE id NOT IN (
                SELECT MAX(id) FROM memories GROUP BY fact_key
            )
            """
        )
        extra = self._db.execute("SELECT COUNT(*) AS n FROM memories").fetchone()["n"] - MEMORY_CAP
        if extra > 0:
            self._db.execute(
                """
                DELETE FROM memories WHERE id IN (
                    SELECT id FROM memories ORDER BY approved_at, id LIMIT ?
                )
                """,
                (extra,),
            )
