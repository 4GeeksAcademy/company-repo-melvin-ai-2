"""JSON contract for POST /api/incidents/analyze. Matches uis/web AnalysisSummary."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class IncidentTotals(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int


class IncidentInvalidBreakdown(BaseModel):
    missing_location_id: int
    invalid_or_missing_category: int
    empty_description: int
    closed_case_no_score: int
    missing_reporter_id: int
    score_out_of_range: int


class IncidentCategoryRow(BaseModel):
    category: str
    count: int
    percentage: float


class IncidentStatusRow(BaseModel):
    status: str
    count: int
    percentage: float


class IncidentScoreRow(BaseModel):
    score: int
    label: str
    count: int


class IncidentSatisfaction(BaseModel):
    scored_cases: int
    closed_cases: int
    average_score: Optional[float] = None
    by_score: list[IncidentScoreRow]


class IncidentAnalysisResponse(BaseModel):
    source_file: str
    totals: IncidentTotals
    invalid_breakdown: IncidentInvalidBreakdown
    by_category: list[IncidentCategoryRow]
    by_status: list[IncidentStatusRow]
    satisfaction: IncidentSatisfaction
