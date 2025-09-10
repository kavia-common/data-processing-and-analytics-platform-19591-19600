from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .routers import uploads, analytics, reports, visualize
from .core.config import get_settings
from .core.docs import openapi_tags


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    - Registers middleware
    - Includes routers
    - Configures OpenAPI metadata
    """
    settings = get_settings()
    app = FastAPI(
        title="Data Processing and Analytics API",
        description="Upload datasets, compute statistics, process records, visualize results, and send summary reports via email.",
        version="1.0.0",
        contact={"name": "Support", "email": settings.SUPPORT_EMAIL},
        license_info={"name": "MIT"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(uploads.router, prefix="/api", tags=["Uploads"])
    app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
    app.include_router(reports.router, prefix="/api", tags=["Reports"])
    app.include_router(visualize.router, prefix="/api", tags=["Visualization"])

    @app.get("/", summary="Health Check", tags=["Health"])
    def health_check() -> dict[str, str]:
        """
        Health check endpoint to verify the API is running.

        Returns:
            A dictionary with a health message.
        """
        return {"message": "Healthy"}

    # Customize OpenAPI with predefined tags
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema["tags"] = openapi_tags
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]

    return app


app = create_app()

# Note: to run locally on port 3001:
# uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload
