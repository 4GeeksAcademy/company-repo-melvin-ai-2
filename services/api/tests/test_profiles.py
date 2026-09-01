"""GET/PUT /profiles/me — signed-in operator profile."""

from __future__ import annotations

from app.users import service as users_service
from tests.factories import bearer


def test_profile_me_read_and_update_name_phone_address(
    client, carlos, carlos_token
):
    read = client.get("/profiles/me", headers=bearer(carlos_token)).json()
    assert read.get("user_id") == carlos["id"]
    assert read.get("name") == "Carlos Restrepo"

    client.put(
        "/profiles/me",
        headers=bearer(carlos_token),
        json={
            "name": "Carlos Restrepo — Poblado",
            "phone": "+57 300 555 0101",
            "address": "Envigado, Colombia",
        },
    )

    profile = users_service.get_profile_for_user(carlos["id"])
    assert profile is not None
    assert profile["name"] == "Carlos Restrepo — Poblado"
    assert profile["phone"] == "+57 300 555 0101"
    assert profile["address"] == "Envigado, Colombia"


def test_profile_partial_update_leaves_unspecified_fields(
    client, carlos, carlos_token
):
    original = users_service.get_profile_for_user(carlos["id"])
    assert original is not None

    client.put(
        "/profiles/me",
        headers=bearer(carlos_token),
        json={"phone": "+57 300 555 0199"},
    )

    profile = users_service.get_profile_for_user(carlos["id"])
    assert profile is not None
    assert profile["phone"] == "+57 300 555 0199"
    # Unspecified fields are left as stored; this is a patch, not a replace.
    assert profile["name"] == original["name"]
    assert profile["address"] == original["address"]


def test_profile_without_token_is_not_returned_or_changed(client, carlos):
    before = users_service.get_profile_for_user(carlos["id"])
    assert before is not None

    read = client.get("/profiles/me").json()
    assert read.get("user_id") != carlos["id"]

    client.put(
        "/profiles/me",
        json={"name": "Anonymous Kitchen"},
    )

    after = users_service.get_profile_for_user(carlos["id"])
    assert after is not None
    assert after["name"] == before["name"]
