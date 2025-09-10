from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request model for generating reports."""
    filename: str = Field(..., description="Dataset filename to generate report from")
    include_columns: Optional[List[str]] = Field(
        None, description="Optional list of columns to include in stats"
    )
    format: Literal["text", "json"] = Field(
        "text", description="Report output format"
    )


class ReportResponse(BaseModel):
    """Response model for a generated report."""
    filename: str = Field(..., description="Source dataset filename")
    report_path: str = Field(..., description="Absolute path to saved report file")
    format: Literal["text", "json"] = Field(..., description="Report format")
