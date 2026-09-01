"""Lucía admin seed decisions."""

from __future__ import annotations

from app.auth import store
from app.auth.seed import seed_auth_if_empty, seed_lucia_admin
from app.users import service as users_service
from tests.factories import LUCIA_EMAIL, LUCIA_PASSWORD, create_carlos


def test_seed_skipped_without_admin_credentials(monkeypatch):
    monkeypatch.setattr("app.auth.config.seed_admin_email", lambda: "")
    monkeypatch.setattr("app.auth.config.seed_admin_password", lambda: "")

    assert seed_lucia_admin() == "skipped"
    assert store.count_users() == 0


def test_seed_creates_lucia_as_admin_once(monkeypatch):
    monkeypatch.setattr("app.auth.config.seed_admin_email", lambda: LUCIA_EMAIL)
    monkeypatch.setattr("app.auth.config.seed_admin_password", lambda: LUCIA_PASSWORD)

    assert seed_lucia_admin() == "created"
    assert seed_lucia_admin() == "exists"

    user = users_service.get_user_by_email(LUCIA_EMAIL)
    assert user is not None
    assert user["role"] == "admin"
    profile = users_service.get_profile_for_user(user["id"])
    assert profile is not None
    assert profile["name"] == "Lucía Fernández"


def test_seed_auth_if_empty_leaves_existing_operator(monkeypatch):
    create_carlos()
    monkeypatch.setattr("app.auth.config.seed_admin_email", lambda: LUCIA_EMAIL)
    monkeypatch.setattr("app.auth.config.seed_admin_password", lambda: LUCIA_PASSWORD)

    assert seed_auth_if_empty() == "exists"
    # A non-empty auth DB must not insert a second admin beside Carlos.
    assert users_service.get_user_by_email(LUCIA_EMAIL) is None
