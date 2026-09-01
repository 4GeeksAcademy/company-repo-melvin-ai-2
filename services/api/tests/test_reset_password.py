"""POST /auth/reset-password — one-time, unexpired recovery."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.auth import store
from app.auth.passwords import verify_password
from app.auth.reset import create_reset_token, hash_reset_token
from app.users import service as users_service
from tests.factories import LUCIA_PASSWORD


def test_reset_password_with_valid_token_changes_hash_and_consumes_token(
    client, lucia
):
    raw = create_reset_token(lucia["id"])
    new_password = "NewBrasa12"

    client.post(
        "/auth/reset-password",
        json={"token": raw, "new_password": new_password},
    )

    updated = users_service.get_user_by_id(lucia["id"])
    assert updated is not None
    assert verify_password(new_password, updated["hashed_password"])
    assert not verify_password(LUCIA_PASSWORD, updated["hashed_password"])

    row = store.get_password_reset_by_hash(hash_reset_token(raw))
    assert row is not None
    # used_at is the one-time flag; a second consume must see this set.
    assert row["used_at"] is not None


def test_reset_password_token_cannot_be_reused(client, lucia):
    raw = create_reset_token(lucia["id"])
    first_new = "FirstReset12"
    second_new = "SecondReset12"

    client.post(
        "/auth/reset-password",
        json={"token": raw, "new_password": first_new},
    )
    client.post(
        "/auth/reset-password",
        json={"token": raw, "new_password": second_new},
    )

    updated = users_service.get_user_by_id(lucia["id"])
    assert updated is not None
    # Replay keeps the first new password; the second request must not win.
    assert verify_password(first_new, updated["hashed_password"])
    assert not verify_password(second_new, updated["hashed_password"])


def test_expired_or_garbage_reset_token_leaves_password_unchanged(client, lucia):
    raw = create_reset_token(lucia["id"])
    row = store.get_password_reset_by_hash(hash_reset_token(raw))
    assert row is not None
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    store.update_password_reset(row["id"], {"expires_at": past})

    client.post(
        "/auth/reset-password",
        json={"token": raw, "new_password": "ExpiredTry12"},
    )
    client.post(
        "/auth/reset-password",
        json={"token": "not-a-real-reset-token", "new_password": "GarbageTry12"},
    )

    updated = users_service.get_user_by_id(lucia["id"])
    assert updated is not None
    assert verify_password(LUCIA_PASSWORD, updated["hashed_password"])
