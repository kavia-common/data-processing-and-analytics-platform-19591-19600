from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..schemas.reports import ReportRequest, ReportResponse
from ..services.report_service import ReportService
from ..utils.dependencies import get_report_service

router = APIRouter()


@router.post(
    "/generate",
    summary="Generate a report",
    description="Create a report (text or JSON) from a dataset including basic stats.",
    response_model=ReportResponse,
)
# PUBLIC_INTERFACE
def generate_report(
    req: ReportRequest,
    svc: ReportService = get_report_service,
) -> ReportResponse:
    """
    Generate a report for the dataset and save it to the reports directory.
    """
    try:
        path = svc.generate(req.filename, include_columns=req.include_columns, fmt=req.format)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ReportResponse(filename=req.filename, report_path=str(path), format=req.format)


@router.get(
    "/download",
    summary="Download a report",
    description="Download a previously generated report by filename.",
)
# PUBLIC_INTERFACE
def download_report(
    report_filename: str = Query(..., description="Report filename"),
    svc: ReportService = get_report_service,
) -> FileResponse:
    """
    Return a saved report file for download.
    """
    path: Path = svc.get_path(report_filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path=str(path), filename=path.name)
