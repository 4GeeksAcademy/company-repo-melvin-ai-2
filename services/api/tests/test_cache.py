"""Catalog TTL cache: shared reads, cleared on writes, never session data."""

from __future__ import annotations

import database
from app.cache import catalog_cache
from tests.factories import bearer


def test_ttl_drops_a_catalog_entry_after_expiry(monkeypatch):
    clock = {"now": 1_000.0}
    monkeypatch.setattr("app.cache.time.monotonic", lambda: clock["now"])
    catalog_cache.set("suppliers:list:*|*", [{"id": 1}], 60)
    assert catalog_cache.get("suppliers:list:*|*") == [{"id": 1}]
    clock["now"] = 1_061.0
    assert catalog_cache.get("suppliers:list:*|*") is None


def test_supplier_list_skips_tinydb_until_a_write(client, lucia, lucia_token, monkeypatch):
    calls = {"n": 0}
    real = database.list_suppliers

    def counted(**kwargs):
        calls["n"] += 1
        return real(**kwargs)

    monkeypatch.setattr("routes.suppliers.database.list_suppliers", counted)
    headers = bearer(lucia_token)
    first = client.get("/suppliers", headers=headers)
    second = client.get("/suppliers", headers=headers)
    assert first.status_code == 200
    assert second.json() == first.json()
    assert calls["n"] == 1

    created = client.post(
        "/suppliers",
        headers=headers,
        json={
            "name": "Carbon del Valle",
            "country": "Colombia",
            "categories": ["carbon_y_combustible"],
            "rate_per_unit": 12000,
            "currency": "COP",
        },
    )
    assert created.status_code == 201
    third = client.get("/suppliers", headers=headers)
    names = {row["name"] for row in third.json()}
    assert "Carbon del Valle" in names
    assert calls["n"] == 2


def test_auth_me_is_not_served_from_the_catalog_cache(client, lucia, carlos, lucia_token, carlos_token):
    lucia_me = client.get("/auth/me", headers=bearer(lucia_token)).json()
    carlos_me = client.get("/auth/me", headers=bearer(carlos_token)).json()
    assert lucia_me["email"] != carlos_me["email"]
    assert catalog_cache.get("auth:me") is None
