"""Postgres engine for Brasaland inventory (Supabase). TinyDB auth is separate."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

from app.inventory import models as _models  # noqa: F401 — register tables

API_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(API_ROOT / ".env")

_engine = None


def _normalize_database_url(url: str) -> str:
    """Percent-encode the password so pooler URIs with !, [], etc. still parse."""
    url = (url or "").strip()
    if not url or url.startswith("sqlite"):
        return url
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, hostpart = rest.split("@", 1)
    if ":" not in creds:
        return url
    user, password = creds.split(":", 1)
    if password.startswith("[") and password.endswith("]") and len(password) > 2:
        password = password[1:-1]
    return f"{scheme}://{user}:{quote(password, safe='')}@{hostpart}"


def database_url() -> str:
    return _normalize_database_url(os.getenv("DATABASE_URL") or "")


def _with_ssl(url: str) -> str:
    if url.startswith("sqlite"):
        return url
    if "sslmode" in url:
        return url
    return f"{url}{'&' if '?' in url else '?'}sslmode=require"


def get_engine():
    global _engine
    url = database_url()
    if not url:
        raise RuntimeError(
            "Missing DATABASE_URL. Copy services/api/.env.example to .env "
            "and set the Supabase Transaction pooler URI."
        )
    if _engine is None:
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            _with_ssl(url),
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def reset_engine() -> None:
    """Test helper: drop the cached engine."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def get_inventory_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def init_inventory_db() -> str:
    """Create tables and seed demo ingredients if the inventory DB is empty."""
    url = database_url()
    if not url:
        return "skipped"

    from app.inventory.seed import seed_inventory_if_empty

    SQLModel.metadata.create_all(get_engine())
    with Session(get_engine()) as session:
        return seed_inventory_if_empty(session)
