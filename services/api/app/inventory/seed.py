"""Demo ingredients, deliveries, and kitchen exits for Brasaland."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.auth import store as auth_store
from app.inventory.models import Ingredient, IngredientEntry, IngredientExit

SEED_INGREDIENTS = [
    {
        "name": "Beef brisket",
        "sku": "BRS-BEEF-001",
        "unit": "kg",
        "category": "meat",
        "country": "CO",
    },
    {
        "name": "Pork ribs",
        "sku": "BRS-PORK-001",
        "unit": "kg",
        "category": "meat",
        "country": "US",
    },
    {
        "name": "Chimichurri sauce",
        "sku": "BRS-SAUCE-001",
        "unit": "litre",
        "category": "sauce",
        "country": "CO",
    },
    {
        "name": "House BBQ sauce",
        "sku": "BRS-SAUCE-002",
        "unit": "litre",
        "category": "sauce",
        "country": "US",
    },
    {
        "name": "Yuca (cassava)",
        "sku": "BRS-PROD-001",
        "unit": "kg",
        "category": "produce",
        "country": "CO",
    },
    {
        "name": "Takeaway box (M)",
        "sku": "BRS-PKG-001",
        "unit": "unit",
        "category": "packaging",
        "country": "CO",
    },
]


def _creator_user_uuid() -> str:
    users = auth_store.list_users()
    if not users:
        return "1"
    return str(users[0]["id"])


def seed_inventory_if_empty(session: Session) -> str:
    existing = session.exec(select(Ingredient)).first()
    if existing is not None:
        return "exists"

    user_uuid = _creator_user_uuid()
    now = datetime.now(timezone.utc)
    by_sku: dict[str, Ingredient] = {}
    for row in SEED_INGREDIENTS:
        ingredient = Ingredient(**row)
        session.add(ingredient)
        session.flush()
        by_sku[ingredient.sku] = ingredient

    entries = [
        IngredientEntry(
            ingredient_id=by_sku["BRS-BEEF-001"].id,
            quantity=50.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=1,
            created_at=now - timedelta(days=5),
            user_uuid=user_uuid,
        ),
        IngredientEntry(
            ingredient_id=by_sku["BRS-BEEF-001"].id,
            quantity=30.0,
            supplier_name="Carnes del Valle S.A.",
            location_id=1,
            created_at=now - timedelta(days=3),
            user_uuid=user_uuid,
        ),
        IngredientEntry(
            ingredient_id=by_sku["BRS-PORK-001"].id,
            quantity=40.0,
            supplier_name="MiamiMeat Co.",
            location_id=11,
            created_at=now - timedelta(days=4),
            user_uuid=user_uuid,
        ),
        IngredientEntry(
            ingredient_id=by_sku["BRS-SAUCE-001"].id,
            quantity=20.0,
            supplier_name="Salsas Artesanales Ltda.",
            location_id=2,
            created_at=now - timedelta(days=2),
            user_uuid=user_uuid,
        ),
    ]
    exits = [
        IngredientExit(
            ingredient_id=by_sku["BRS-BEEF-001"].id,
            quantity=15.0,
            reason="consumption",
            location_id=1,
            created_at=now - timedelta(days=2),
            user_uuid=user_uuid,
        ),
        IngredientExit(
            ingredient_id=by_sku["BRS-BEEF-001"].id,
            quantity=5.0,
            reason="waste",
            location_id=1,
            created_at=now - timedelta(days=1),
            user_uuid=user_uuid,
        ),
        IngredientExit(
            ingredient_id=by_sku["BRS-PORK-001"].id,
            quantity=8.0,
            reason="consumption",
            location_id=11,
            created_at=now - timedelta(hours=12),
            user_uuid=user_uuid,
        ),
    ]
    for row in entries + exits:
        session.add(row)
    session.commit()
    return "created"
