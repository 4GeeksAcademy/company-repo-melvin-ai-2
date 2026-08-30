"""Seed Lucía Fernández as the Brasaland procurement admin."""

from __future__ import annotations

from app.auth import config
from app.users import service as users_service
from app.users.schemas import UserRole

LUCIA_NAME = "Lucía Fernández"
LUCIA_PHONE = "+57 4 444 1208"
LUCIA_ADDRESS = "Brasaland Digital, Medellín, Colombia"


def seed_lucia_admin() -> str:
    """Create Lucía if missing. Returns 'created', 'exists', or 'skipped'."""
    email = config.seed_admin_email()
    password = config.seed_admin_password()
    if not email or not password:
        return "skipped"

    existing = users_service.get_user_by_email(email)
    if existing is not None:
        return "exists"

    users_service.create_user(
        email=email,
        password=password,
        role=UserRole.admin,
        name=LUCIA_NAME,
        phone=LUCIA_PHONE,
        address=LUCIA_ADDRESS,
    )
    return "created"


def seed_auth_if_empty() -> str:
    from app.auth import store

    if store.count_users() > 0:
        return "exists"
    return seed_lucia_admin()


def seed_command() -> None:
    import sys

    from app.errors import PersistenceError

    try:
        status = seed_lucia_admin()
        print(f"Auth seed: {status}")
    except PersistenceError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError:
        print("Error: could not write account data.", file=sys.stderr)
        raise SystemExit(1)
    except Exception:
        print("Error: could not complete the account seed.", file=sys.stderr)
        raise SystemExit(1)
