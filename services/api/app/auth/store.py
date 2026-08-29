"""TinyDB persistence for Brasaland User and Profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from tinydb import Query, TinyDB

from app.errors import PersistenceError

AUTH_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "auth.json"


def get_auth_db() -> TinyDB:
    try:
        AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return TinyDB(AUTH_DB_PATH)
    except OSError as exc:
        raise PersistenceError("Could not open the account directory.") from exc


def _users():
    return get_auth_db().table("users")


def _profiles():
    return get_auth_db().table("profiles")


def _with_id(doc_id: int, doc: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(doc)
    payload["id"] = doc_id
    return payload


def count_users() -> int:
    return len(_users())


def list_users() -> List[Dict[str, Any]]:
    rows = [_with_id(doc.doc_id, dict(doc)) for doc in _users().all()]
    rows.sort(key=lambda row: row.get("email") or "")
    return rows


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    doc = _users().get(doc_id=user_id)
    if doc is None:
        return None
    return _with_id(user_id, dict(doc))


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    User = Query()
    doc = _users().get(User.email == email.strip().lower())
    if doc is None:
        return None
    return _with_id(doc.doc_id, dict(doc))


def insert_user(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(data)
    payload["email"] = str(payload["email"]).strip().lower()
    doc_id = _users().insert(payload)
    return _with_id(doc_id, payload)


def update_user(user_id: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing = _users().get(doc_id=user_id)
    if existing is None:
        return None
    merged = dict(existing)
    merged.update(patch)
    if "email" in merged:
        merged["email"] = str(merged["email"]).strip().lower()
    _users().update(merged, doc_ids=[user_id])
    return _with_id(user_id, merged)


def delete_user(user_id: int) -> bool:
    removed = _users().remove(doc_ids=[user_id])
    return bool(removed)


def get_profile_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
    Profile = Query()
    doc = _profiles().get(Profile.user_id == user_id)
    if doc is None:
        return None
    return _with_id(doc.doc_id, dict(doc))


def insert_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(data)
    doc_id = _profiles().insert(payload)
    return _with_id(doc_id, payload)


def update_profile_by_user_id(
    user_id: int, patch: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    existing = get_profile_by_user_id(user_id)
    if existing is None:
        return None
    profile_id = existing["id"]
    merged = dict(_profiles().get(doc_id=profile_id) or {})
    merged.update(patch)
    merged["user_id"] = user_id
    _profiles().update(merged, doc_ids=[profile_id])
    return _with_id(profile_id, merged)


def delete_profile_by_user_id(user_id: int) -> None:
    Profile = Query()
    _profiles().remove(Profile.user_id == user_id)


def _resets():
    return get_auth_db().table("password_resets")


def insert_password_reset(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(data)
    doc_id = _resets().insert(payload)
    return _with_id(doc_id, payload)


def get_password_reset_by_hash(token_hash: str) -> Optional[Dict[str, Any]]:
    Reset = Query()
    doc = _resets().get(Reset.token_hash == token_hash)
    if doc is None:
        return None
    return _with_id(doc.doc_id, dict(doc))


def update_password_reset(reset_id: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing = _resets().get(doc_id=reset_id)
    if existing is None:
        return None
    merged = dict(existing)
    merged.update(patch)
    _resets().update(merged, doc_ids=[reset_id])
    return _with_id(reset_id, merged)


def mark_unused_resets_used(user_id: int, used_at: str) -> None:
    Reset = Query()
    rows = _resets().search((Reset.user_id == user_id) & (Reset.used_at == None))  # noqa: E711
    for doc in rows:
        merged = dict(doc)
        merged["used_at"] = used_at
        _resets().update(merged, doc_ids=[doc.doc_id])


def delete_resets_for_user(user_id: int) -> None:
    Reset = Query()
    _resets().remove(Reset.user_id == user_id)
