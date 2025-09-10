from __future__ import annotations

class AppError(Exception):
    """Base application error with a user-friendly message."""

    def __init__(self, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class FileProcessingError(AppError):
    """Raised when file I/O or parsing fails."""
    pass


class EmailSendError(AppError):
    """Raised when email sending fails."""
    pass
