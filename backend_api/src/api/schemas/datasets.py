from __future__ import annotations

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response model for dataset upload."""

    filename: str = Field(..., description="Saved filename")
    path: str = Field(..., description="Absolute path to saved file")
    size_bytes: int = Field(..., description="Size in bytes")


class DatasetInfo(BaseModel):
    """Dataset metadata for listings."""

    filename: str = Field(..., description="Dataset filename")
    path: str = Field(..., description="Absolute path to file")
    size_bytes: int = Field(..., description="File size in bytes")
    modified_at: float = Field(..., description="Last modified timestamp (epoch seconds)")
