from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.viz import VizRequest, VizResponse
from ..services.viz_service import VisualizationService
from ..utils.dependencies import get_viz_service

router = APIRouter()


@router.post(
    "/plot",
    summary="Generate plot",
    description="Generate a histogram or boxplot for a numeric column and save it as a PNG image.",
    response_model=VizResponse,
)
# PUBLIC_INTERFACE
def generate_plot(
    req: VizRequest,
    svc: VisualizationService = get_viz_service,
) -> VizResponse:
    """
    Generate a plot image for a given column and return the saved file path.
    """
    try:
        img_path = svc.generate_plot(filename=req.filename, column=req.column, kind=req.kind, bins=req.bins)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return VizResponse(filename=req.filename, column=req.column, kind=req.kind, image_path=str(img_path))
