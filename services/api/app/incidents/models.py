"""Stored Brasaland incidents. The public id is generated here, not taken from the CSV."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentRecord(SQLModel, table=True):
    __tablename__ = "managed_incidents"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    category: str = Field(index=True)
    status: str = Field(index=True)
    origin: str = Field(index=True)
    branch: str = Field(index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    seed_key: Optional[str] = Field(default=None, unique=True, index=True)
