"""POST /auth/change-password — authenticated rotation only."""

from __future__ import annotations

from app.auth.passwords import verify_password
from app.users import service as users_service
from tests.factories import CARLOS_PASSWORD, bearer


def test_change_password_with_current_password_updates_hash(
    client, carlos, carlos_token
):
    new_password = "NewKitchen12"
    client.post(
        "/auth/change-password",
        headers=bearer(carlos_token),
        json={
            "current_password": CARLOS_PASSWORD,
            "new_password": new_password,
        },
    )

    updated = users_service.get_user_by_id(carlos["id"])
    assert updated is not None
    assert verify_password(new_password, updated["hashed_password"])
    assert not verify_password(CARLOS_PASSWORD, updated["hashed_password"])


def test_change_password_wrong_current_leaves_hash_unchanged(
    client, carlos, carlos_token
):
    client.post(
        "/auth/change-password",
        headers=bearer(carlos_token),
        json={
            "current_password": "not-carlos-password",
            "new_password": "ShouldNotStick12",
        },
    )

    updated = users_service.get_user_by_id(carlos["id"])
    assert updated is not None
    # Wrong current password is not a session problem; the stored hash stays.
    assert verify_password(CARLOS_PASSWORD, updated["hashed_password"])


def test_change_password_without_session_leaves_hash_unchanged(client, carlos):
    client.post(
        "/auth/change-password",
        json={
            "current_password": CARLOS_PASSWORD,
            "new_password": "NoSession12",
        },
    )

    updated = users_service.get_user_by_id(carlos["id"])
    assert updated is not None
    assert verify_password(CARLOS_PASSWORD, updated["hashed_password"])
