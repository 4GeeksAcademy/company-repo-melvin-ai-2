"""POST /users — public registration decisions."""

from __future__ import annotations

from app.auth import store
from app.users import service as users_service
from tests.factories import CARLOS_EMAIL, CARLOS_PASSWORD


def test_register_creates_operator_with_user_role_and_profile(client):
    client.post(
        "/users",
        json={
            "email": CARLOS_EMAIL,
            "password": CARLOS_PASSWORD,
            "name": "Carlos Restrepo",
            "phone": "+57 4 444 2210",
            "address": "Poblado, Medellín, Colombia",
        },
    )

    user = users_service.get_user_by_email(CARLOS_EMAIL)
    assert user is not None
    # Public signup must mint a kitchen operator, never procurement admin.
    assert user["role"] == "user"
    profile = users_service.get_profile_for_user(user["id"])
    assert profile is not None
    assert profile["name"] == "Carlos Restrepo"


def test_register_duplicate_email_does_not_create_second_user(client):
    payload = {
        "email": CARLOS_EMAIL,
        "password": CARLOS_PASSWORD,
        "name": "Carlos Restrepo",
    }
    client.post("/users", json=payload)
    client.post("/users", json=payload)

    matches = [row for row in store.list_users() if row["email"] == CARLOS_EMAIL]
    # Duplicate email is rejected in the store, not by counting HTTP 409s.
    assert len(matches) == 1


def test_register_empty_fields_does_not_store_a_user(client):
    client.post("/users", json={"email": "", "password": ""})

    assert store.count_users() == 0
    assert users_service.get_user_by_email("") is None
