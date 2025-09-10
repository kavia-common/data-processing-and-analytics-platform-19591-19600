from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .storage_service import StorageService
from ..utils.errors import AppException


class ProcessingService:
    """
    Service that performs record processing on CSV or JSONL datasets in a streaming fashion.
    Supported steps:
      - dropna: remove rows with any empty values
      - dedupe: drop exact duplicate rows
      - uppercase_strings: uppercase string fields
    """

    def __init__(self, storage: StorageService) -> None:
        self.storage = storage

    def _detect_format(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".csv":
            return "csv"
        if ext in (".jsonl", ".ndjson"):
            return "jsonl"
        raise AppException("Unsupported file format for processing. Use CSV or JSONL.")

    def _iter_rows(self, path: Path) -> Tuple[List[str], Iterable[Dict[str, object]]]:
        fmt = self._detect_format(path)
        if fmt == "csv":
            f = path.open("r", newline="", encoding="utf-8")
            reader = csv.DictReader(f)
            return list(reader.fieldnames or []), reader
        else:
            f = path.open("r", encoding="utf-8")
            first = f.readline()
            if not first:
                return [], []
            obj = json.loads(first)
            fieldnames = list(obj.keys())

            def gen():
                yield obj
                for line in f:
                    if not line.strip():
                        continue
                    yield json.loads(line)

            return fieldnames, gen()

    def _apply_steps(self, row: Dict[str, object], steps: List[str]) -> Dict[str, object] | None:
        # dropna
        if "dropna" in steps:
            if any(v is None or v == "" for v in row.values()):
                return None

        # uppercase_strings
        if "uppercase_strings" in steps:
            for k, v in list(row.items()):
                if isinstance(v, str):
                    row[k] = v.upper()

        return row

    # PUBLIC_INTERFACE
    def process(self, filename: str, steps: List[str], chunk_size: int = 1000) -> tuple[Path, int]:
        """
        Process dataset rows with the specified steps, writing a CSV output file.
        Returns (output_path, processed_count).
        Raises FileNotFoundError if dataset doesn't exist.
        Raises ValueError for invalid parameters.
        """
        src = self.storage.get_upload_path(filename)
        if not src.exists():
            raise FileNotFoundError(filename)
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        fieldnames, rows_iter = self._iter_rows(src)
        if not fieldnames:
            # empty file
            out = self.storage.get_output_path(stem=Path(filename).stem + "_processed", suffix=".csv")
            out.write_text("", encoding="utf-8")  # create empty
            return out, 0

        out = self.storage.get_output_path(stem=Path(filename).stem + "_processed", suffix=".csv")

        # We'll write CSV regardless of input format for uniformity
        processed = 0
        seen_rows = set()  # for dedupe
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            buffer: List[Dict[str, object]] = []
            for row in rows_iter:
                row = dict(row)  # ensure dict
                # dedupe check
                if "dedupe" in steps:
                    sig = tuple(row.get(k) for k in fieldnames)
                    if sig in seen_rows:
                        continue
                    seen_rows.add(sig)

                new_row = self._apply_steps(row, steps)
                if new_row is None:
                    continue
                buffer.append(new_row)
                if len(buffer) >= chunk_size:
                    writer.writerows(buffer)
                    processed += len(buffer)
                    buffer.clear()
            if buffer:
                writer.writerows(buffer)
                processed += len(buffer)

        return out, processed
