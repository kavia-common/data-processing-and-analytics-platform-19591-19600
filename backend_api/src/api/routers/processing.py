from __future__ import annotations



from fastapi import APIRouter, HTTPException

from ..schemas.processing import ProcessRequest, ProcessResponse
from ..services.processing_service import ProcessingService
from ..utils.dependencies import get_processing_service

router = APIRouter()


@router.post(
    "/run",
    summary="Run record processing",
    description="Apply a set of processing steps to the dataset and write an output file.",
    response_model=ProcessResponse,
)
# PUBLIC_INTERFACE
def run_processing(
    req: ProcessRequest,
    svc: ProcessingService = get_processing_service,
) -> ProcessResponse:
    """
    Execute the record processing pipeline based on the specified steps and chunk size.
    """
    try:
        output_path, processed_count = svc.process(
            filename=req.filename,
            steps=req.steps,
            chunk_size=req.chunk_size,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ProcessResponse(
        filename=req.filename,
        output_path=str(output_path),
        processed_records=processed_count,
        steps_applied=req.steps,
    )
