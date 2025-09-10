from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Tuple

from ..utils.errors import AppException
from .storage_service import StorageService


def _safe_float(value: str) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


class DataService:
    """
    Service for reading datasets and computing basic statistics.
    Supports CSV and JSON Lines (jsonl) files.
    """

    def __init__(self, storage: StorageService) -> None:
        self.storage = storage

    def _detect_format(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".csv":
            return "csv"
        if ext in (".jsonl", ".ndjson"):
            return "jsonl"
        raise ValueError("Unsupported file format. Supported: .csv, .jsonl")

    def _iter_rows(self, path: Path) -> Tuple[List[str], Iterable[Dict[str, str]]]:
        fmt = self._detect_format(path)
        if fmt == "csv":
            f = path.open("r", newline="", encoding="utf-8")
            reader = csv.DictReader(f)
            # We rely on the file object staying open while the caller iterates.
            return list(reader.fieldnames or []), reader
        else:
            # jsonl
            f = path.open("r", encoding="utf-8")
            # We need to infer fieldnames from first line
            first = f.readline()
            if not first:
                return [], []
            try:
                obj = json.loads(first)
            except json.JSONDecodeError as exc:
                raise AppException("Invalid JSONL file") from exc
            fieldnames = list(obj.keys())
            # generator that yields first parsed obj and subsequent lines
            def gen():
                yield {k: obj.get(k) for k in fieldnames}
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    yield {k: rec.get(k) for k in fieldnames}

            return fieldnames, gen()

    # PUBLIC_INTERFACE
    def compute_statistics(self, filename: str, columns: Optional[List[str]] = None) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Compute basic statistics for numeric columns.
        Returns mapping: column -> {count, mean, std, min, max, median}
        Raises FileNotFoundError if dataset doesn't exist.
        Raises ValueError for invalid parameters.
        """
        path = self.storage.get_upload_path(filename)
        if not path.exists():
            raise FileNotFoundError(filename)

        fieldnames, rows_iter = self._iter_rows(path)
        if not fieldnames:
            return {}

        target_cols = columns if columns else fieldnames

        numeric_values: Dict[str, List[float]] = {c: [] for c in target_cols}

        for row in rows_iter:
            for col in target_cols:
                val = _safe_float(row.get(col))
                if val is not None:
                    numeric_values[col].append(val)

        result: Dict[str, Dict[str, Optional[float]]] = {}
        for col, values in numeric_values.items():
            if not values:
                result[col] = {
                    "count": 0,
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                    "median": None,
                }
                continue

            n = len(values)
            mu = sum(values) / n
            # population standard deviation
            var = sum((x - mu) ** 2 for x in values) / n
            std = var ** 0.5
            result[col] = {
                "count": n,
                "mean": mu,
                "std": std,
                "min": min(values),
                "max": max(values),
                "median": median(values),
            }
        return result

    # PUBLIC_INTERFACE
    def get_dataset_info(self, filename: str) -> Dict[str, Optional[object]]:
        """
        Return a quick summary: row count and column names.
        Raises FileNotFoundError if dataset doesn't exist.
        """
        path = self.storage.get_upload_path(filename)
        if not path.exists():
            raise FileNotFoundError(filename)

        fieldnames, rows_iter = self._iter_rows(path)
        count = 0
        for _ in rows_iter:
            count += 1
        return {"rows": count, "columns": fieldnames}
