from __future__ import annotations

from typing import Any, Dict

from fastapi.openapi.utils import get_openapi as _fastapi_get_openapi
from fastapi import FastAPI


def get_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate a custom OpenAPI schema with predefined tags and metadata overrides.
    """
    openapi_schema = _fastapi_get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["tags"] = [
        {"name": "Datasets", "description": "Upload, list, download, and delete datasets."},
        {"name": "Statistics", "description": "Compute and fetch dataset statistics."},
        {"name": "Processing", "description": "Run record processing pipelines."},
        {"name": "Reports", "description": "Generate and download reports."},
        {"name": "Notifications", "description": "Send notifications such as emails."},
        {"name": "Visualization", "description": "Generate simple SVG plots."},
        {"name": "Documentation", "description": "API documentation endpoints."},
    ]
    return openapi_schema
