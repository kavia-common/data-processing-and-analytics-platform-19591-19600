from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..schemas.stats import StatsRequest, StatsResponse, ColumnStats
from ..services.data_service import DataService
from ..utils.dependencies import get_data_service

router = APIRouter()


@router.post(
    "/compute",
    summary="Compute statistics",
    description="Compute basic statistics (count, mean, std, min, max, median) for selected numeric columns.",
    response_model=StatsResponse,
)
# PUBLIC_INTERFACE
def compute_stats(
    req: StatsRequest,
    data_service: DataService = get_data_service,
) -> StatsResponse:
    """
    Compute statistics on the provided dataset file for the specified columns.
    """
    try:
        result = data_service.compute_statistics(req.filename, req.columns or None)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    stats: List[ColumnStats] = [
        ColumnStats(
            column=k,
            count=v["count"],
            mean=v["mean"],
            std=v["std"],
            min=v["min"],
            max=v["max"],
            median=v["median"],
        )
        for k, v in result.items()
    ]
    return StatsResponse(filename=req.filename, stats=stats)


@router.get(
    "/summary",
    summary="Quick dataset summary",
    description="Return row count and column list for a dataset.",
    response_model=Dict[str, Optional[object]],
)
# PUBLIC_INTERFACE
def dataset_summary(
    filename: str = Query(..., description="Dataset filename"),
    data_service: DataService = get_data_service,
) -> Dict[str, Optional[object]]:
    """
    Provide a quick summary: number of rows and columns present in the dataset.
    """
    try:
        info = data_service.get_dataset_info(filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return info
