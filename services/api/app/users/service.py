"""User and profile domain services for Brasaland credentials."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.auth import store
from app.auth.passwords import hash_password
from app.users.schemas import UserRole


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def public_user(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "email": row["email"],
        "is_active": bool(row.get("is_active", True)),
        "role": row["role"],
        "created_at": row["created_at"],
    }


def public_profile(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row.get("name"),
        "phone": row.get("phone"),
        "address": row.get("address"),
    }


def create_user(
    *,
    email: str,
    password: str,
    role: UserRole = UserRole.user,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
) -> Dict[str, Any]:
    if store.get_user_by_email(email):
        raise ValueError("email already registered")
    user = store.insert_user(
        {
            "email": email,
            "hashed_password": hash_password(password),
            "is_active": True,
            "role": role.value,
            "created_at": _utc_now().isoformat(),
        }
    )
    store.insert_profile(
        {
            "user_id": user["id"],
            "name": name,
            "phone": phone,
            "address": address,
        }
    )
    return user


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    return store.get_user(user_id)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return store.get_user_by_email(email)


def list_users() -> list[Dict[str, Any]]:
    return store.list_users()


def update_user(user_id: int, patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "email" in patch and patch["email"]:
        existing = store.get_user_by_email(patch["email"])
        if existing is not None and existing["id"] != user_id:
            raise ValueError("email already registered")
    return store.update_user(user_id, patch)


def delete_user(user_id: int) -> bool:
    if store.get_user(user_id) is None:
        return False
    store.delete_resets_for_user(user_id)
    store.delete_profile_by_user_id(user_id)
    return store.delete_user(user_id)


def get_profile_for_user(user_id: int) -> Optional[Dict[str, Any]]:
    return store.get_profile_by_user_id(user_id)


def update_profile_for_user(
    user_id: int, patch: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    return store.update_profile_by_user_id(user_id, patch)


def ensure_profile(user_id: int) -> Dict[str, Any]:
    profile = store.get_profile_by_user_id(user_id)
    if profile is not None:
        return profile
    return store.insert_profile(
        {"user_id": user_id, "name": None, "phone": None, "address": None}
    )
