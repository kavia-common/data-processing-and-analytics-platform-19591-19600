from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .routers import datasets, stats, processing, reports, notifications, viz
from .utils.errors import AppException, app_exception_handler
from .utils.settings import get_settings
from .utils.openapi import get_openapi_schema

# App-level logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("backend_api")


def _ensure_directories(settings) -> None:
    """
    Ensure required directories (data, uploads, outputs) exist at startup.
    """
    for p in [
        Path(settings.DATA_DIR),
        Path(settings.UPLOAD_DIR),
        Path(settings.OUTPUT_DIR),
        Path(settings.REPORTS_DIR),
        Path(settings.VIZ_DIR),
    ]:
        p.mkdir(parents=True, exist_ok=True)


def _create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    settings = get_settings()
    _ensure_directories(settings)

    app = FastAPI(
        title="Data Processing and Analytics Platform API",
        description=(
            "Backend API for dataset upload, processing, statistics, summary reporting, "
            "email notifications, and result visualization."
        ),
        version="1.0.0",
        contact={"name": "Engineering", "email": "devnull@example.com"},
        license_info={"name": "Proprietary", "identifier": "UNLICENSED"},
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)

    # Routers
    app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
    app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
    app.include_router(processing.router, prefix="/api/processing", tags=["Processing"])
    app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
    app.include_router(viz.router, prefix="/api/viz", tags=["Visualization"])

    # Health endpoint
    @app.get(
        "/",
        summary="Health Check",
        description="Simple health check endpoint.",
        responses={
            200: {"description": "Service is healthy"},
        },
    )
    # PUBLIC_INTERFACE
    def health_check() -> Dict[str, str]:
        """Health check endpoint returning service status."""
        return {"message": "Healthy"}

    # Expose OpenAPI schema explicitly for interface consumers and CI capture
    @app.get(
        "/openapi.json",
        summary="OpenAPI Schema",
        description="Return the OpenAPI schema for this service.",
        tags=["Documentation"],
    )
    # PUBLIC_INTERFACE
    def custom_openapi() -> JSONResponse:
        """
        Return the custom OpenAPI schema with standardized metadata and tags.
        """
        schema = get_openapi_schema(app)
        return JSONResponse(schema)

    return app


app = _create_app()
