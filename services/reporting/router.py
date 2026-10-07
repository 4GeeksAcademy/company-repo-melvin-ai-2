"""Bearer endpoints that start or read the weekly location pipeline.

KPI math stays in ``data/pipelines``. These routes do not read
``services/telemetry`` and do not call ``GET /telemetry/report``.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "services" / "api"
for entry in (str(API_ROOT), str(ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from app.auth.deps import get_current_user  # noqa: E402
from data.pipelines.pipeline import (  # noqa: E402
    latest_weekly_performance_run,
    read_weekly_location_performance,
    request_weekly_location_performance_run,
)

router = APIRouter(prefix="/reporting", tags=["reporting"])


class PipelineRunRequest(BaseModel):
    week_start: date | None = None


class LocationWeek(BaseModel):
    location_id: str
    country: str
    total_purchase_cost: float
    total_waste_cost: float
    waste_ratio: float
    stockout_events_count: int
    price_alert_events_count: int
    currency: str


class WeeklyLocationPerformance(BaseModel):
    week_start: date | None
    locations: list[LocationWeek]


@router.get("/pipeline-runs/latest")
def latest_run(_user=Depends(get_current_user)) -> dict:
    row = latest_weekly_performance_run()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No weekly performance run has been recorded yet.",
        )
    return row


@router.post("/pipeline-runs")
def start_run(
    body: PipelineRunRequest | None = None,
    _user=Depends(get_current_user),
) -> dict:
    week = body.week_start if body else None
    try:
        return request_weekly_location_performance_run(week)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The weekly report could not be rebuilt. Try again.",
        ) from None


@router.get("/weekly-location-performance", response_model=WeeklyLocationPerformance)
def weekly_location_performance(
    week_start: date | None = None,
    _user=Depends(get_current_user),
) -> dict:
    return read_weekly_location_performance(week_start)
