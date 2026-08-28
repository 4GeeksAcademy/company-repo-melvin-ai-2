"""Load JWT and seed settings from the environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(API_ROOT / ".env")


def _require(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Missing {name}. Copy services/api/.env.example to .env and set it."
        )
    return value


def secret_key() -> str:
    return _require("SECRET_KEY")


def access_token_expire_minutes() -> int:
    raw = (os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "60").strip()
    try:
        minutes = int(raw)
    except ValueError as exc:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer.") from exc
    if minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0.")
    return minutes


def seed_admin_email() -> str:
    return (os.getenv("SEED_ADMIN_EMAIL") or "").strip().lower()


def seed_admin_password() -> str:
    return os.getenv("SEED_ADMIN_PASSWORD") or ""


def reset_token_expire_minutes() -> int:
    raw = (os.getenv("RESET_TOKEN_EXPIRE_MINUTES") or "30").strip()
    try:
        minutes = int(raw)
    except ValueError as exc:
        raise RuntimeError("RESET_TOKEN_EXPIRE_MINUTES must be an integer.") from exc
    if minutes < 15 or minutes > 60:
        raise RuntimeError("RESET_TOKEN_EXPIRE_MINUTES must be between 15 and 60.")
    return minutes


def public_app_url() -> str:
    return (os.getenv("PUBLIC_APP_URL") or "http://localhost:3101").rstrip("/")


def resend_api_key() -> str:
    return (os.getenv("RESEND_API_KEY") or "").strip()


def resend_from_email() -> str:
    return (os.getenv("RESEND_FROM_EMAIL") or "Brasaland <beth.t@example.com>").strip()
