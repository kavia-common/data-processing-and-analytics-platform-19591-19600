"""
Production-ready utility module derived from the provided script.

This module provides utilities for:
- File I/O (JSON reading, text writing)
- Numeric computations (safe divide, stats, mean)
- Data processing helpers (flatten dict, find top k, factorial, checksum, dict merge)
- Date parsing and CSV parsing
- Retry wrapper
- Lightweight email sender stub (for dev/testing)
- DataProcessor class for iterating over JSON arrays from disk

Design notes:
- All public functions/classes are marked with PUBLIC_INTERFACE and include docstrings.
- Functions have type hints and error handling.
- No environment-specific configuration is hard-coded. Defaults are provided; callers should pass config or set env vars.
- Logging is used instead of prints for diagnostics. Public API returns values or raises exceptions.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple, TypeVar

logger = logging.getLogger(__name__)
LOG_LEVEL = os.getenv("STANDALONE_TOOLS_LOG_LEVEL", "INFO").upper()
if not logger.handlers:
    logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

# Global defaults (kept minimal; callers should override via parameters when possible)
MAX_RETRIES_DEFAULT = 3
DEFAULT_EMAIL = "noreply@example.com"

T = TypeVar("T")


# PUBLIC_INTERFACE
def read_json_file(path: str | os.PathLike[str]) -> Any:
    """Read and parse JSON file from the given path.

    Raises:
        FileNotFoundError: when the path does not exist
        json.JSONDecodeError: when the content is not valid JSON
        OSError: on underlying IO errors

    Returns:
        Parsed JSON content (dict, list, etc.)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File {p} not found")
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# PUBLIC_INTERFACE
def safe_divide(a: float, b: float) -> float:
    """Safely divide a by b, returning +inf on division by zero."""
    try:
        return a / b
    except ZeroDivisionError:
        return float("inf")


# PUBLIC_INTERFACE
def compute_mean(values: Sequence[float]) -> float:
    """Compute arithmetic mean. Returns 0.0 for empty sequence."""
    if not values:
        return 0.0
    return float(sum(values)) / float(len(values))


# PUBLIC_INTERFACE
def compute_stats(numbers: Sequence[float]) -> Dict[str, Optional[float] | int]:
    """Compute basic statistics for a sequence of numbers.

    Returns:
        dict with keys: count, sum, mean, std (population), min, max
        For empty input: count=0, sum=0, mean=0, std=0, min=None, max=None
    """
    if not numbers:
        return {"count": 0, "sum": 0.0, "mean": 0.0, "std": 0.0, "min": None, "max": None}
    count = len(numbers)
    total = float(sum(numbers))
    mean = total / count
    variance = sum((x - mean) ** 2 for x in numbers) / count
    std = math.sqrt(variance)
    return {
        "count": count,
        "sum": total,
        "mean": mean,
        "std": std,
        "min": min(numbers),
        "max": max(numbers),
    }


@dataclass
class DataProcessor:
    """Lightweight data processor that loads a JSON array from <path>/data.json and iterates its items."""

    path: str | os.PathLike[str]
    data: List[Mapping[str, Any]] = field(default_factory=list)
    index: int = 0

    # PUBLIC_INTERFACE
    def load(self) -> None:
        """Load JSON array from <path>/data.json. On missing file, keeps data empty."""
        try:
            full = Path(self.path) / "data.json"
            obj = read_json_file(full)
            if isinstance(obj, list):
                # Only accept list of mappings/items
                self.data = [x for x in obj if isinstance(x, Mapping)]
                self.index = 0
            else:
                logger.warning("Expected a JSON array in %s; got %s. Using empty data.", full, type(obj).__name__)
                self.data = []
                self.index = 0
        except FileNotFoundError:
            logger.info("File not found at %s; continuing with empty data", self.path)
            self.data = []
            self.index = 0
        except Exception as exc:
            logger.exception("Error loading data: %s", exc)
            self.data = []
            self.index = 0

    # PUBLIC_INTERFACE
    def next(self) -> Mapping[str, Any]:
        """Return next item; cycles from the start when the end is reached.

        Raises:
            StopIteration: when there are no items loaded
        """
        if not self.data:
            raise StopIteration("No data available")
        if self.index >= len(self.data):
            self.index = 0
        item = self.data[self.index]
        self.index += 1
        return item

    # PUBLIC_INTERFACE
    def filter(self, predicate: Callable[[Mapping[str, Any]], bool]) -> None:
        """Filter in-place keeping items where predicate(item) is True."""
        self.data = [item for item in self.data if predicate(item)]
        # Reset iteration index after filter
        self.index = 0

    # PUBLIC_INTERFACE
    def summary(self, value_key: str = "value") -> Dict[str, float | int]:
        """Compute a basic summary using the provided numeric value_key."""
        if not self.data:
            return {"count": 0, "total": 0.0, "avg": 0.0}
        total = 0.0
        count = len(self.data)
        for x in self.data:
            try:
                total += float(x.get(value_key, 0) or 0)
            except (TypeError, ValueError):
                continue
        avg = total / count if count else 0.0
        return {"count": count, "total": total, "avg": avg}


# PUBLIC_INTERFACE
def send_email(recipient: Optional[str], subject: str, body: str, default_sender: str = DEFAULT_EMAIL) -> bool:
    """Send an email (development stub).

    In production, prefer using a proper NotificationService.
    Validates recipient and returns True to indicate that the action would be performed.
    """
    recipient = recipient or default_sender
    if not isinstance(recipient, str) or "@" not in recipient:
        logger.error("Invalid recipient: %r", recipient)
        return False
    logger.info("Sending email to %s with subject '%s'", recipient, subject)
    return True


# PUBLIC_INTERFACE
def retry_operation(fn: Callable[..., T], *args: Any, retries: int = MAX_RETRIES_DEFAULT, **kwargs: Any) -> Optional[T]:
    """Run fn with retries. Returns fn result on success, None on repeated failure."""
    last_exc: Optional[Exception] = None
    for i in range(retries):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - generic utility
            last_exc = exc
            logger.warning("Attempt %d failed: %s", i + 1, exc)
    logger.error("Operation failed after %d attempts: %s", retries, last_exc)
    return None


# PUBLIC_INTERFACE
def parse_csv(path: str | os.PathLike[str]) -> List[Dict[str, str]]:
    """Parse a CSV file into a list of dict rows."""
    p = Path(path)
    data: List[Dict[str, str]] = []
    with p.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            data.append(dict(row))
    return data


# PUBLIC_INTERFACE
def flatten_dict(d: Mapping[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dict with dot-separated paths."""
    items: Dict[str, Any] = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, Mapping):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


# PUBLIC_INTERFACE
def find_top_k(numbers: Sequence[float], k: int = 3) -> List[float]:
    """Return top-k numbers in descending order."""
    if k <= 0:
        return []
    return sorted(numbers, reverse=True)[:k]


# PUBLIC_INTERFACE
def factorial(n: int) -> int:
    """Compute factorial using iterative approach to avoid deep recursion.

    Raises:
        ValueError: if n < 0
    """
    if n < 0:
        raise ValueError("Negative factorial not defined")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


class _Conn:
    def query(self, q: str) -> List[Dict[str, Any]]:
        return []


# PUBLIC_INTERFACE
def connect_to_db(uri: Optional[str]) -> _Conn:
    """Return a dummy connection object. Raise on missing uri.

    In production, integrate with a real DB client and load credentials from environment.
    """
    if not uri:
        raise ValueError("No uri provided")
    return _Conn()


# PUBLIC_INTERFACE
def run_heavy_computation(x: int) -> int:
    """Compute the sum of squares from 0..x-1 efficiently using formula."""
    if x <= 0:
        return 0
    # Sum of squares formula: n(n+1)(2n+1)/6 for n = x-1 -> but we want 0..x-1 squares
    n = x - 1
    return int(n * (n + 1) * (2 * n + 1) // 6)


# PUBLIC_INTERFACE
def compute_checksum(data: str) -> int:
    """Compute simple checksum (sum of code points mod 256)."""
    s = 0
    for c in data:
        s += ord(c)
    return s % 256


# PUBLIC_INTERFACE
def merge_dicts(a: MutableMapping[str, Any], b: Mapping[str, Any]) -> Dict[str, Any]:
    """Deep-merge dict b into dict a and return a new dict."""
    res: Dict[str, Any] = dict(a)
    for k, v in b.items():
        if k in res and isinstance(res[k], dict) and isinstance(v, dict):
            res[k] = merge_dicts(res[k], v)  # type: ignore[arg-type]
        else:
            res[k] = v
    return res


# PUBLIC_INTERFACE
def parse_date(s: str, fmt: str = "%Y-%m-%d") -> dt.datetime:
    """Parse a date string using the given strptime format."""
    return dt.datetime.strptime(s, fmt)


# PUBLIC_INTERFACE
def write_output(path: str | os.PathLike[str], content: str) -> None:
    """Write text content to a file, creating parent directories as needed."""
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# PUBLIC_INTERFACE
def process_records(records: Iterable[Mapping[str, Any]], value_key: str = "value") -> List[Any]:
    """Process records by doubling the value when active is truthy.

    Missing value_key is treated as 0.
    """
    processed: List[Any] = []
    for r in records:
        val = r.get(value_key, 0)
        try:
            num = float(val)
        except (TypeError, ValueError):
            num = 0.0
        if r.get("active"):
            num *= 2
        processed.append(num)
    return processed


# PUBLIC_INTERFACE
def validate_user(u: Mapping[str, Any]) -> bool:
    """Validate a user dict: password presence and length >= 8, valid email if provided."""
    pwd = u.get("password")
    if not pwd or not isinstance(pwd, str) or len(pwd) < 8:
        return False
    email = u.get("email")
    if email is not None and (not isinstance(email, str) or "@" not in email):
        return False
    return True
