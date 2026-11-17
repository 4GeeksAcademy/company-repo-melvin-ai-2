"""Create the RFP tables on the same Postgres engine as inventory."""

from __future__ import annotations

from app.inventory.db import database_url, get_engine
from app.rfp import models as _models  # noqa: F401
from sqlmodel import SQLModel


def init_rfp_db() -> str:
    if not database_url():
        return "skipped"
    SQLModel.metadata.create_all(get_engine())
    return "ready"
