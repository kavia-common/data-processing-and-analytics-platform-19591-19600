from __future__ import annotations

import csv
import os
import uuid
from typing import Dict, List, Tuple

from ..core.config import get_settings
from ..core.exceptions import FileProcessingError
from ..core.log import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    PUBLIC_INTERFACE
    Handle storing and loading dataset files and results.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def _dataset_path(self, file_id: str) -> str:
        return os.path.join(self.settings.DATA_DIR, f"{file_id}.csv")

    def _results_path(self, file_id: str, suffix: str) -> str:
        return os.path.join(self.settings.RESULTS_DIR, f"{file_id}{suffix}")

    def save_upload(self, filename: str, file_bytes: bytes) -> Tuple[str, int, int, bool]:
        """
        Save an uploaded CSV to disk and return metadata: (file_id, rows, cols, has_header)
        """
        file_id = uuid.uuid4().hex
        path = self._dataset_path(file_id)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(file_bytes)
            rows, cols, has_header = self._inspect_csv(path)
            logger.info(
                "Saved upload %s as %s.csv with rows=%s cols=%s header=%s",
                filename,
                file_id,
                rows,
                cols,
                has_header,
            )
            return file_id, rows, cols, has_header
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save upload: %s", exc)
            raise FileProcessingError("Failed to save uploaded file", detail=str(exc)) from exc

    def _inspect_csv(self, path: str) -> Tuple[int, int, bool]:
        """
        Inspect CSV to get row/column counts and detect header.
        """
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                sample = f.read(4096)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
                has_header = csv.Sniffer().has_header(sample) if sample else True
                reader = csv.reader(f, dialect)
                row_count = 0
                first_row_len = 0
                for i, row in enumerate(reader):
                    if i == 0:
                        first_row_len = len(row)
                    row_count += 1
                cols = first_row_len
                if has_header and row_count > 0:
                    row_count -= 1
                return row_count, cols, bool(has_header)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to inspect csv: %s", exc)
            raise FileProcessingError("Invalid or unreadable CSV file", detail=str(exc)) from exc

    def read_csv(self, file_id: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Read a CSV by file_id and return headers and rows.
        If no header exists, generate generic column names col_0..col_n
        """
        path = self._dataset_path(file_id)
        if not os.path.exists(path):
            raise FileProcessingError(f"Dataset not found for id={file_id}")
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                sample = f.read(4096)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
                has_header = csv.Sniffer().has_header(sample) if sample else True
                f.seek(0)
                reader = csv.reader(f, dialect)
                rows: List[List[str]] = list(reader)
                if not rows:
                    return [], []
                if has_header:
                    header = rows[0]
                    data_rows = rows[1:]
                else:
                    header = [f"col_{i}" for i in range(len(rows[0]))]
                    data_rows = rows
                dict_rows: List[Dict[str, str]] = [dict(zip(header, r)) for r in data_rows]
                return header, dict_rows
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to read csv: %s", exc)
            raise FileProcessingError("Failed to read dataset", detail=str(exc)) from exc

    def save_results_json(self, file_id: str, name: str, content: str) -> str:
        """
        Save a JSON text result file and return its absolute path.
        """
        path = self._results_path(file_id, f"_{name}.json")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save results json: %s", exc)
            raise FileProcessingError("Failed to save results", detail=str(exc)) from exc

    def save_results_image(self, file_id: str, name: str, img_bytes: bytes) -> str:
        """
        Save an image result file and return its absolute path.
        """
        path = self._results_path(file_id, f"_{name}.png")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(img_bytes)
            return path
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save results image: %s", exc)
            raise FileProcessingError("Failed to save visualization", detail=str(exc)) from exc
