from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from fastapi.responses import FileResponse

from ..schemas.datasets import DatasetInfo, UploadResponse
from ..services.storage_service import StorageService
from ..utils.dependencies import get_storage_service

router = APIRouter()


@router.post(
    "/upload",
    summary="Upload a dataset file",
    description="Upload a CSV or JSON Lines (jsonl) dataset. The file will be stored on the server.",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
# PUBLIC_INTERFACE
async def upload_dataset(
    file: UploadFile = File(..., description="CSV or JSONL dataset file"),
    storage: StorageService = get_storage_service,
) -> UploadResponse:
    """
    Upload a dataset file (CSV or JSONL) and persist it in the uploads directory.
    """
    saved = await storage.save_upload(file)
    return UploadResponse(filename=saved.name, path=str(saved), size_bytes=saved.stat().st_size)


@router.get(
    "",
    summary="List uploaded datasets",
    description="List dataset files available in the uploads directory.",
    response_model=List[DatasetInfo],
)
# PUBLIC_INTERFACE
def list_datasets(
    storage: StorageService = get_storage_service,
) -> List[DatasetInfo]:
    """
    Return a list of uploaded datasets with basic metadata.
    """
    items: List[DatasetInfo] = []
    for p in storage.list_uploads():
        items.append(
            DatasetInfo(
                filename=p.name,
                path=str(p),
                size_bytes=p.stat().st_size,
                modified_at=p.stat().st_mtime,
            )
        )
    return items


@router.get(
    "/download",
    summary="Download dataset file",
    description="Download a dataset by filename.",
    responses={404: {"description": "File not found"}},
)
# PUBLIC_INTERFACE
def download_dataset(
    filename: str = Query(..., description="Dataset filename"),
    storage: StorageService = get_storage_service,
) -> FileResponse:
    """
    Return a dataset file for download.
    """
    file_path: Path = storage.get_upload_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename=file_path.name)


@router.delete(
    "",
    summary="Delete dataset",
    description="Delete a dataset by filename from uploads.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "File not found"}},
)
# PUBLIC_INTERFACE
def delete_dataset(
    filename: str = Query(..., description="Dataset filename"),
    storage: StorageService = get_storage_service,
) -> None:
    """
    Delete a dataset from the uploads directory.
    """
    file_path = storage.get_upload_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink()
