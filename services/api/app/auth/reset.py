"""One-time password-reset tokens stored hashed in TinyDB."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.auth import config, store


class ResetTokenError(ValueError):
    """Invalid, expired, or already-used reset token."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_reset_token(user_id: int) -> str:
    raw = secrets.token_urlsafe(32)
    now = _utc_now()
    store.mark_unused_resets_used(user_id, now.isoformat())
    expires = now + timedelta(minutes=config.reset_token_expire_minutes())
    store.insert_password_reset(
        {
            "token_hash": hash_reset_token(raw),
            "user_id": user_id,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "used_at": None,
        }
    )
    return raw


def consume_reset_token(raw: str) -> int:
    row = store.get_password_reset_by_hash(hash_reset_token(raw.strip()))
    if row is None:
        raise ResetTokenError("invalid or expired reset token")
    if row.get("used_at"):
        raise ResetTokenError("invalid or expired reset token")
    expires_at = datetime.fromisoformat(str(row["expires_at"]))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _utc_now():
        raise ResetTokenError("invalid or expired reset token")
    used_at = _utc_now().isoformat()
    store.update_password_reset(row["id"], {"used_at": used_at})
    store.mark_unused_resets_used(row["user_id"], used_at)
    return int(row["user_id"])
