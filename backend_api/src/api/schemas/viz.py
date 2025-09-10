from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, PositiveInt


class VizRequest(BaseModel):
    """Request to generate a visualization."""

    filename: str = Field(..., description="Dataset filename")
    column: str = Field(..., description="Column to visualize")
    kind: Literal["hist", "box"] = Field("hist", description="Type of plot")
    bins: Optional[PositiveInt] = Field(20, description="Histogram bins (only for hist)")


class VizResponse(BaseModel):
    """Response containing visualization path."""

    filename: str = Field(..., description="Dataset filename")
    column: str = Field(..., description="Column used")
    kind: Literal["hist", "box"] = Field(..., description="Plot type")
    image_path: str = Field(..., description="Saved image path")
