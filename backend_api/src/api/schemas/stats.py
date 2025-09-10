from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class StatsRequest(BaseModel):
    """Request to compute statistics on a dataset."""

    filename: str = Field(..., description="Dataset filename previously uploaded")
    columns: Optional[List[str]] = Field(None, description="Subset of columns to compute stats for (numeric only)")


class ColumnStats(BaseModel):
    """Statistics for a single column."""

    column: str = Field(..., description="Column name")
    count: int = Field(..., description="Non-null value count")
    mean: Optional[float] = Field(None, description="Mean")
    std: Optional[float] = Field(None, description="Standard deviation")
    min: Optional[float] = Field(None, description="Minimum")
    max: Optional[float] = Field(None, description="Maximum")
    median: Optional[float] = Field(None, description="Median")


class StatsResponse(BaseModel):
    """Response containing computed statistics."""

    filename: str = Field(..., description="Dataset filename")
    stats: List[ColumnStats] = Field(..., description="List of per-column statistics")
