from __future__ import annotations

from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception type."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# PUBLIC_INTERFACE
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    FastAPI exception handler for AppException, returning JSON error payloads.
    """
    payload: Dict[str, Any] = {"error": exc.message}
    return JSONResponse(status_code=exc.status_code, content=payload)
