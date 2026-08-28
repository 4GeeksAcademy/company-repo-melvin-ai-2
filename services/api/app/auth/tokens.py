"""Signed JWT access tokens for Brasaland sessions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.auth import config

ALGORITHM = "HS256"


def create_access_token(*, user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.access_token_expire_minutes()
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.secret_key(), algorithm=ALGORITHM)


def user_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(token, config.secret_key(), algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("missing sub")
        return int(sub)
    except (JWTError, ValueError, TypeError) as exc:
        raise ValueError("invalid token") from exc
