"""GET /auth/me — session identity the internal UIs trust."""

from __future__ import annotations

from tests.factories import LUCIA_EMAIL, bearer


def test_me_returns_signed_in_operator_email_role_and_profile(
    client, lucia, lucia_token
):
    response = client.get("/auth/me", headers=bearer(lucia_token))
    payload = response.json()

    assert payload.get("email") == LUCIA_EMAIL
    assert payload.get("role") == "admin"
    assert payload.get("profile", {}).get("name") == "Lucía Fernández"
    assert payload.get("profile", {}).get("user_id") == lucia["id"]


def test_me_without_authorization_is_not_authenticated(client, lucia):
    response = client.get("/auth/me")
    payload = response.json()

    # Missing Bearer must not surface Lucía's identity or profile.
    assert payload.get("email") != LUCIA_EMAIL
    assert "profile" not in payload or payload.get("profile") is None


def test_me_inactive_operator_is_not_authenticated(client, lucia, lucia_token):
    from app.users import service as users_service

    users_service.update_user(lucia["id"], {"is_active": False})
    response = client.get("/auth/me", headers=bearer(lucia_token))
    payload = response.json()

    assert payload.get("email") != LUCIA_EMAIL


def test_me_with_malformed_token_is_not_authenticated(client, lucia):
    response = client.get("/auth/me", headers=bearer("totally.invalid.token"))
    payload = response.json()

    assert payload.get("email") != LUCIA_EMAIL
    assert "profile" not in payload or payload.get("profile") is None
