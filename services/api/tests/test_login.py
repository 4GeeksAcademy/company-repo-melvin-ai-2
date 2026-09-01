"""POST /auth/login — who receives a Brasaland session."""

from __future__ import annotations

from app.auth.tokens import user_id_from_token
from app.users import service as users_service
from tests.factories import LUCIA_EMAIL, LUCIA_PASSWORD


def test_login_issues_token_for_valid_credentials(client, lucia):
    response = client.post(
        "/auth/login",
        json={"email": LUCIA_EMAIL, "password": LUCIA_PASSWORD},
    )

    token = response.json().get("access_token")
    # Decision: a session exists only if the JWT identifies Lucía.
    assert token
    assert user_id_from_token(token) == lucia["id"]


def test_login_inactive_operator_does_not_receive_a_token(client, lucia):
    users_service.update_user(lucia["id"], {"is_active": False})

    response = client.post(
        "/auth/login",
        json={"email": LUCIA_EMAIL, "password": LUCIA_PASSWORD},
    )

    payload = response.json()
    # Inactive operators keep their password but must not receive a session.
    assert "access_token" not in payload or not payload.get("access_token")


def test_login_wrong_password_does_not_issue_a_token(client, lucia):
    response = client.post(
        "/auth/login",
        json={"email": LUCIA_EMAIL, "password": "not-lucia-password"},
    )

    payload = response.json()
    assert "access_token" not in payload or not payload.get("access_token")
