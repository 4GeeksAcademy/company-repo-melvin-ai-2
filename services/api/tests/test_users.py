"""/users directory — self-or-admin decisions."""

from __future__ import annotations

from app.users import service as users_service
from tests.factories import CARLOS_EMAIL, LUCIA_EMAIL, bearer


def test_list_users_returns_registered_brasaland_emails(
    client, lucia, carlos, lucia_token
):
    response = client.get("/users", headers=bearer(lucia_token))
    payload = response.json()
    emails = {row["email"] for row in payload}

    assert LUCIA_EMAIL in emails
    assert CARLOS_EMAIL in emails


def test_list_users_with_only_one_operator_has_length_one(client, carlos, carlos_token):
    response = client.get("/users", headers=bearer(carlos_token))
    payload = response.json()

    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["email"] == CARLOS_EMAIL


def test_list_users_without_token_does_not_return_the_directory(client, lucia):
    response = client.get("/users")
    payload = response.json()

    emails = (
        {row.get("email") for row in payload} if isinstance(payload, list) else set()
    )
    # Error bodies are objects; a list of emails would mean the directory leaked.
    assert LUCIA_EMAIL not in emails


def test_get_user_self(client, carlos, carlos_token):
    response = client.get(f"/users/{carlos['id']}", headers=bearer(carlos_token))
    payload = response.json()

    assert payload.get("email") == CARLOS_EMAIL
    assert payload.get("id") == carlos["id"]


def test_get_user_admin_can_read_another_operator(
    client, lucia, carlos, lucia_token
):
    response = client.get(f"/users/{carlos['id']}", headers=bearer(lucia_token))
    payload = response.json()

    assert payload.get("email") == CARLOS_EMAIL


def test_get_user_operator_cannot_read_another_operator(
    client, lucia, carlos, carlos_token
):
    response = client.get(f"/users/{lucia['id']}", headers=bearer(carlos_token))
    payload = response.json()

    assert payload.get("email") != LUCIA_EMAIL


def test_update_user_self_email(client, carlos, carlos_token):
    new_email = "carlos.kitchen@brasaland.com"
    client.put(
        f"/users/{carlos['id']}",
        headers=bearer(carlos_token),
        json={"email": new_email},
    )

    updated = users_service.get_user_by_id(carlos["id"])
    assert updated is not None
    assert updated["email"] == new_email


def test_update_user_non_admin_cannot_become_admin(client, carlos, carlos_token):
    client.put(
        f"/users/{carlos['id']}",
        headers=bearer(carlos_token),
        json={"role": "admin"},
    )

    updated = users_service.get_user_by_id(carlos["id"])
    assert updated is not None
    # Role stays user even if the JSON included role=admin.
    assert updated["role"] == "user"


def test_update_user_operator_cannot_edit_another_operator(
    client, lucia, carlos, carlos_token
):
    client.put(
        f"/users/{lucia['id']}",
        headers=bearer(carlos_token),
        json={"email": "hijacked@brasaland.com"},
    )

    lucia_row = users_service.get_user_by_id(lucia["id"])
    assert lucia_row is not None
    # Carlos cannot re-point Lucía's login email.
    assert lucia_row["email"] == LUCIA_EMAIL


def test_delete_user_self(client, carlos, carlos_token):
    client.delete(f"/users/{carlos['id']}", headers=bearer(carlos_token))

    assert users_service.get_user_by_id(carlos["id"]) is None


def test_delete_user_admin_can_remove_another_operator(
    client, lucia, carlos, lucia_token
):
    client.delete(f"/users/{carlos['id']}", headers=bearer(lucia_token))

    assert users_service.get_user_by_id(carlos["id"]) is None
    assert users_service.get_user_by_id(lucia["id"]) is not None


def test_delete_user_operator_cannot_remove_another_operator(
    client, lucia, carlos, carlos_token
):
    client.delete(f"/users/{lucia['id']}", headers=bearer(carlos_token))

    assert users_service.get_user_by_id(lucia["id"]) is not None
