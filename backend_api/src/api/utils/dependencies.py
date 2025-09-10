from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from ..services.storage_service import StorageService
from ..services.data_service import DataService
from ..services.processing_service import ProcessingService
from ..services.report_service import ReportService
from ..services.notification_service import NotificationService
from ..services.viz_service import VisualizationService


@lru_cache
def _storage() -> StorageService:
    return StorageService()


def get_storage_service() -> StorageService:
    """FastAPI dependency that returns a StorageService instance."""
    return _storage()


def get_data_service(storage: StorageService = Depends(get_storage_service)) -> DataService:
    """FastAPI dependency that returns a DataService instance."""
    return DataService(storage=storage)


def get_processing_service(storage: StorageService = Depends(get_storage_service)) -> ProcessingService:
    """FastAPI dependency that returns a ProcessingService instance."""
    return ProcessingService(storage=storage)


def get_report_service(
    storage: StorageService = Depends(get_storage_service),
    data_service: DataService = Depends(get_data_service),
) -> ReportService:
    """FastAPI dependency that returns a ReportService instance."""
    return ReportService(storage=storage, data_service=data_service)


def get_notification_service() -> NotificationService:
    """FastAPI dependency that returns a NotificationService instance."""
    return NotificationService()


def get_viz_service(storage: StorageService = Depends(get_storage_service)) -> VisualizationService:
    """FastAPI dependency that returns a VisualizationService instance."""
    return VisualizationService(storage=storage)
