"""Brasaland operators used by the auth test suite."""

from __future__ import annotations

from typing import Dict

from fastapi.testclient import TestClient

from app.users import service as users_service
from app.users.schemas import UserRole

LUCIA_EMAIL = "lucia.fernandez@brasaland.com"
LUCIA_PASSWORD = "Procura12"
CARLOS_EMAIL = "carlos.restrepo@brasaland.com"
CARLOS_PASSWORD = "Brasaland1"


def create_lucia() -> Dict:
    return users_service.create_user(
        email=LUCIA_EMAIL,
        password=LUCIA_PASSWORD,
        role=UserRole.admin,
        name="Lucía Fernández",
        phone="+57 4 444 1208",
        address="Brasaland Digital, Medellín, Colombia",
    )


def create_carlos() -> Dict:
    return users_service.create_user(
        email=CARLOS_EMAIL,
        password=CARLOS_PASSWORD,
        role=UserRole.user,
        name="Carlos Restrepo",
        phone="+57 4 444 2210",
        address="Poblado, Medellín, Colombia",
    )


def bearer(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def issue_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    payload = response.json()
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise AssertionError("login did not issue an access token")
    return token
