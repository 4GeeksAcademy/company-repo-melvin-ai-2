"""Ingredient inventory decisions: derived stock and no negative exits."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import pytest

from app.inventory.db import get_inventory_session
from app.inventory.seed import seed_inventory_if_empty
from app.inventory.stock import insufficient_stock_message
from tests.factories import bearer


@pytest.fixture
def inventory_ready(tmp_path, client: TestClient, lucia):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'inventory.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    from main import app

    app.dependency_overrides[get_inventory_session] = override_session
    with Session(engine) as session:
        seed_inventory_if_empty(session)
    yield client
    app.dependency_overrides.pop(get_inventory_session, None)


def test_list_products_includes_country_and_derived_stock(
    inventory_ready, lucia, lucia_token
):
    client = inventory_ready
    payload = client.get("/inventory/products", headers=bearer(lucia_token)).json()
    by_sku = {row["sku"]: row for row in payload}

    assert "BRS-BEEF-001" in by_sku
    assert by_sku["BRS-BEEF-001"]["country"] == "CO"
    # 50 + 30 inbound − 15 consumption − 5 waste
    assert by_sku["BRS-BEEF-001"]["current_stock"] == 60.0
    assert "current_stock" in by_sku["BRS-BEEF-001"]
    assert by_sku["BRS-PORK-001"]["country"] == "US"
    assert by_sku["BRS-PORK-001"]["current_stock"] == 32.0


def test_outbound_over_available_is_rejected_before_write(
    inventory_ready, lucia, lucia_token
):
    client = inventory_ready
    products = client.get("/inventory/products", headers=bearer(lucia_token)).json()
    beef = next(row for row in products if row["sku"] == "BRS-BEEF-001")
    requested = beef["current_stock"] + 1

    response = client.post(
        "/inventory/orders/outbound",
        headers=bearer(lucia_token),
        json={
            "ingredient_id": beef["id"],
            "quantity": requested,
            "reason": "consumption",
            "location_id": 1,
        },
    )
    assert response.status_code == 400
    detail = response.json().get("detail")
    assert detail == insufficient_stock_message(
        "Beef brisket", beef["current_stock"], requested
    )

    again = client.get(
        f"/inventory/products/{beef['id']}", headers=bearer(lucia_token)
    ).json()
    assert again["current_stock"] == beef["current_stock"]


def test_orders_list_newest_first_with_ingredient_and_type(
    inventory_ready, lucia, lucia_token
):
    client = inventory_ready
    payload = client.get("/inventory/orders", headers=bearer(lucia_token)).json()

    types = {row["type"] for row in payload}
    assert "entry" in types
    assert "exit" in types
    assert all("ingredient" in row and "country" in row["ingredient"] for row in payload)
    created = [row["created_at"] for row in payload]
    assert created == sorted(created, reverse=True)
    assert any(row.get("reason") == "waste" for row in payload if row["type"] == "exit")


def test_invalid_exit_reason_is_rejected(inventory_ready, lucia, lucia_token):
    client = inventory_ready
    products = client.get("/inventory/products", headers=bearer(lucia_token)).json()
    beef = next(row for row in products if row["sku"] == "BRS-BEEF-001")
    response = client.post(
        "/inventory/orders/outbound",
        headers=bearer(lucia_token),
        json={
            "ingredient_id": beef["id"],
            "quantity": 1,
            "reason": "theft",
            "location_id": 1,
        },
    )
    payload = response.json()
    assert response.status_code == 422
    assert payload.get("id") is None
    assert "detail" in payload


def test_list_products_country_filter(inventory_ready, lucia, lucia_token):
    client = inventory_ready
    payload = client.get(
        "/inventory/products",
        params={"country": "US"},
        headers=bearer(lucia_token),
    ).json()
    assert payload
    assert {row["country"] for row in payload} == {"US"}
    assert "BRS-PORK-001" in {row["sku"] for row in payload}
    assert "BRS-BEEF-001" not in {row["sku"] for row in payload}


def test_inventory_without_session_does_not_list_ingredients(
    inventory_ready, lucia
):
    client = inventory_ready
    payload = client.get("/inventory/products").json()
    skus = (
        {row.get("sku") for row in payload} if isinstance(payload, list) else set()
    )
    assert "BRS-BEEF-001" not in skus
