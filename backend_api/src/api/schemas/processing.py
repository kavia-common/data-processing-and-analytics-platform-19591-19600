from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """Request to process a dataset with a set of steps."""

    filename: str = Field(..., description="Dataset filename to process")
    steps: List[Literal["dropna", "dedupe", "uppercase_strings"]] = Field(
        default_factory=list,
        description="Processing steps to apply in order",
    )
    # Use standard int with ge validation for compatibility
    chunk_size: int = Field(1000, ge=1, description="Chunk size for streaming processing")


class ProcessResponse(BaseModel):
    """Response with processing results."""

    filename: str = Field(..., description="Original dataset filename")
    output_path: str = Field(..., description="Path to the processed output file")
    processed_records: int = Field(..., description="Total processed records count")
    steps_applied: List[str] = Field(..., description="Steps applied in order")
