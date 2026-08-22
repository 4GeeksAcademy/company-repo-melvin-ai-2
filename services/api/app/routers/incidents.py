from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.incidents.analysis import (
    IncidentAnalysisError,
    analyze_text,
    export_results_csv_text,
    result_to_summary,
)
from app.incidents.store import get_last_result, save_last_result

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def _validate_upload(filename: str | None, content_type: str | None) -> None:
    name = (filename or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="A CSV file is required.")
    lower = name.lower()
    if not lower.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Incorrect file format. Upload a .csv file.",
        )
    if content_type and content_type not in {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
        "text/plain",
    }:
        # Browsers vary; extension is the primary check.
        pass


@router.post("/analyze")
async def analyze_incidents(file: UploadFile = File(...)) -> dict:
    _validate_upload(file.filename, file.content_type)

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 encoded.",
        ) from exc

    try:
        result = analyze_text(text, source_name=file.filename or "upload.csv")
    except IncidentAnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if result.total_rows == 0:
        raise HTTPException(
            status_code=400,
            detail="The CSV has a header but no data rows.",
        )

    save_last_result(result)
    return result_to_summary(result)


@router.get("/results/export")
async def export_results() -> Response:
    result = get_last_result()
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis results are available. Upload a CSV first.",
        )

    csv_text = export_results_csv_text(result)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="results.csv"',
        },
    )
