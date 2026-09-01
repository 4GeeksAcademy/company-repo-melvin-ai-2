"""Isolated TinyDB and env for Brasaland auth tests."""

from __future__ import annotations

import os

os.environ["SECRET_KEY"] = "test-secret-key-brasaland-auth-088"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["SEED_ADMIN_EMAIL"] = ""
os.environ["SEED_ADMIN_PASSWORD"] = ""
os.environ["RESEND_API_KEY"] = ""
os.environ["RESET_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["PUBLIC_APP_URL"] = "http://localhost:3101"

import pytest
from fastapi.testclient import TestClient

from tests.factories import (
    CARLOS_EMAIL,
    CARLOS_PASSWORD,
    LUCIA_EMAIL,
    LUCIA_PASSWORD,
    create_carlos,
    create_lucia,
    issue_token,
)


@pytest.fixture(autouse=True)
def isolated_auth_db(tmp_path, monkeypatch):
    monkeypatch.setattr("app.auth.store.AUTH_DB_PATH", tmp_path / "auth.json")
    monkeypatch.setattr("database.DB_PATH", tmp_path / "suppliers.json")
    monkeypatch.setattr("main.count_suppliers", lambda: 1)
    monkeypatch.setattr("main.seed_auth_if_empty", lambda: "skipped")
    yield tmp_path


@pytest.fixture
def client() -> TestClient:
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def lucia():
    return create_lucia()


@pytest.fixture
def carlos():
    return create_carlos()


@pytest.fixture
def lucia_token(client, lucia) -> str:
    return issue_token(client, LUCIA_EMAIL, LUCIA_PASSWORD)


@pytest.fixture
def carlos_token(client, carlos) -> str:
    return issue_token(client, CARLOS_EMAIL, CARLOS_PASSWORD)
