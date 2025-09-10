from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from .storage_service import StorageService
from .data_service import DataService
from ..utils.errors import AppException


def _retry_io(attempts: int = 3, delay: float = 0.1, backoff: float = 2.0):
    """
    Simple retry decorator for transient I/O operations.
    Retries on common OSErrors like PermissionError, FileExistsError, BlockingIOError.

    Note: Keep it lightweight and local to this service to avoid cross-cutting complexity.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            _attempts, _delay = attempts, delay
            last_exc: Optional[Exception] = None
            for _ in range(_attempts):
                try:
                    return func(*args, **kwargs)
                except (OSError, PermissionError, BlockingIOError) as exc:
                    last_exc = exc
                    if _attempts <= 1:
                        break
                    time.sleep(_delay)
                    _attempts -= 1
                    _delay *= backoff
            # On final failure, re-raise as AppException for unified error handling
            raise AppException(f"I/O operation failed after retries: {last_exc}", status_code=500) from last_exc
        return wrapper
    return decorator


class ReportService:
    """
    Service to generate dataset reports (text or JSON) including basic statistics.

    - Uses DataService to compute statistics
    - Supports selecting included columns
    - Supports output formats: text, json
    - Saves reports to StorageService.reports_dir
    """

    def __init__(self, storage: StorageService, data_service: DataService) -> None:
        self.storage = storage
        self.data = data_service

    def _validate_format(self, fmt: str) -> str:
        fmt_norm = (fmt or "text").lower()
        if fmt_norm not in {"text", "json"}:
            raise ValueError("Unsupported report format. Use 'text' or 'json'.")
        return fmt_norm

    def _normalize_columns(self, include_columns: Optional[List[str]]) -> Optional[List[str]]:
        if include_columns is None:
            return None
        if not isinstance(include_columns, list) or any(not isinstance(c, str) for c in include_columns):
            raise ValueError("include_columns must be a list of strings when provided")
        # Deduplicate while preserving order
        seen = set()
        result: List[str] = []
        for c in include_columns:
            if c not in seen:
                result.append(c)
                seen.add(c)
        return result or None

    def _render_text(self, filename: str, stats: Dict[str, Dict[str, Optional[float]]]) -> str:
        lines: List[str] = []
        lines.append(f"Report for: {filename}")
        lines.append("")
        if not stats:
            lines.append("No statistics available (empty dataset or no numeric columns).")
            return "\n".join(lines)

        # Column-aligned text rendering
        lines.append("Column                 Count   Mean        Std         Min         Max         Median")
        lines.append("-" * 90)
        for col, s in stats.items():
            lines.append(
                f"{col:<22} {s['count']:>5}   "
                f"{(s['mean'] if s['mean'] is not None else 'NA'):>10} "
                f"{(s['std'] if s['std'] is not None else 'NA'):>10} "
                f"{(s['min'] if s['min'] is not None else 'NA'):>10} "
                f"{(s['max'] if s['max'] is not None else 'NA'):>10} "
                f"{(s['median'] if s['median'] is not None else 'NA'):>10}"
            )
        return "\n".join(lines)

    @_retry_io()
    def _write_text(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    @_retry_io()
    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _build_output_path(self, filename: str, fmt: str) -> Path:
        suffix = ".txt" if fmt == "text" else ".json"
        stem = f"{Path(filename).stem}_report"
        return self.storage.get_report_path(stem, suffix)

    # PUBLIC_INTERFACE
    def generate(self, filename: str, include_columns: Optional[List[str]] = None, fmt: str = "text") -> Path:
        """
        Generate a report for the dataset.

        Parameters:
        - filename: Dataset filename in uploads
        - include_columns: Optional list of column names to include in stats
        - fmt: 'text' or 'json'

        Returns:
        - Absolute path to the saved report file

        Raises:
        - FileNotFoundError if dataset does not exist
        - ValueError for invalid parameters
        """
        fmt_norm = self._validate_format(fmt)
        cols = self._normalize_columns(include_columns)

        # Compute stats using existing service
        stats = self.data.compute_statistics(filename, cols)

        out_path = self._build_output_path(filename, fmt_norm)

        if fmt_norm == "text":
            content = self._render_text(filename, stats)
            self._write_text(out_path, content)
        else:
            payload = {
                "filename": filename,
                "statistics": stats,
            }
            self._write_json(out_path, payload)

        return out_path

    # PUBLIC_INTERFACE
    def get_path(self, report_filename: str) -> Path:
        """
        Get the absolute path to a report file in the reports directory.
        """
        # Keep it simple: if user passes an absolute path, restrict to reports dir
        p = Path(report_filename)
        if p.is_absolute():
            # Enforce access only within reports directory
            if not str(p).startswith(str(self.storage.reports_dir.resolve())):
                raise AppException("Access to the requested path is not allowed.", status_code=400)
            return p
        # Relative name within reports dir
        return self.storage.reports_dir / report_filename
