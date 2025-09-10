from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr


class UploadResponse(BaseModel):
    file_id: str = Field(..., description="Unique identifier of the uploaded file")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of data rows detected (excluding header if any)")
    columns: int = Field(..., description="Number of columns detected")
    has_header: bool = Field(..., description="Whether a header row was detected")


class StatsRequest(BaseModel):
    file_id: str = Field(..., description="Identifier obtained from upload")
    columns: Optional[List[str]] = Field(None, description="Subset of columns to include in stats; if omitted, all numeric columns are used")


class StatsResponse(BaseModel):
    file_id: str = Field(..., description="Input file identifier")
    summary: Dict[str, Dict[str, float]] = Field(..., description="Per-column descriptive statistics (count, mean, std, min, max)")
    processed_records: int = Field(..., description="Number of records processed")


class ProcessRequest(BaseModel):
    file_id: str = Field(..., description="Identifier obtained from upload")
    filter_expr: Optional[str] = Field(None, description="A simple Python expression using column names, e.g., 'age > 30 and income < 50000'")
    limit: Optional[int] = Field(None, description="Optional maximum number of rows to process")


class ProcessResponse(BaseModel):
    file_id: str = Field(..., description="Input file identifier")
    records: List[Dict[str, object]] = Field(..., description="Processed (filtered/limited) records")
    total_returned: int = Field(..., description="Number of records returned")


class ReportRequest(BaseModel):
    file_id: str = Field(..., description="Identifier obtained from upload")
    recipient_email: Optional[EmailStr] = Field(None, description="Email to send the report to; defaults to configured recipient")
    include_preview: bool = Field(True, description="Whether to include a small data preview in the report")


class ReportResponse(BaseModel):
    file_id: str = Field(..., description="Input file identifier")
    report_id: str = Field(..., description="Generated report identifier")
    emailed_to: Optional[EmailStr] = Field(None, description="Recipient email address if email sent")
    status: str = Field(..., description="Report generation/email status")


class VisualizationRequest(BaseModel):
    file_id: str = Field(..., description="Identifier obtained from upload")
    x: str = Field(..., description="X-axis column")
    y: str = Field(..., description="Y-axis column")
    chart_type: str = Field("scatter", description="Chart type: scatter|line|bar")
