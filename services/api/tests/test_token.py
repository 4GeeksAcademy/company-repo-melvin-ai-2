"""JWT access-token decisions (AUTH-088 expiration regression)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.auth import config
from app.auth.tokens import ALGORITHM, create_access_token, user_id_from_token


def test_fresh_token_identifies_user_and_has_future_expiry():
    token = create_access_token(user_id=7)
    payload = jwt.decode(token, config.secret_key(), algorithms=[ALGORITHM])

    assert user_id_from_token(token) == 7
    assert payload["sub"] == "7"
    exp = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
    # AUTH-088: a live token must carry a future exp, not only a sub.
    assert exp > datetime.now(timezone.utc)


def test_empty_or_garbage_token_is_invalid():
    with pytest.raises(ValueError):
        user_id_from_token("")
    with pytest.raises(ValueError):
        user_id_from_token("not-a-jwt")
    missing_sub = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        config.secret_key(),
        algorithm=ALGORITHM,
    )
    with pytest.raises(ValueError):
        user_id_from_token(missing_sub)


def test_expired_token_is_rejected():
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": "7", "exp": expire},
        config.secret_key(),
        algorithm=ALGORITHM,
    )

    # python-jose rejects exp in the past; that is the session-dead decision.
    with pytest.raises(ValueError):
        user_id_from_token(token)
