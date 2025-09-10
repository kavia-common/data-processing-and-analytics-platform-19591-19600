"""
Small CLI demonstrating the standalone_tools utilities.

Usage:
    python -m api.utils.run_tools_cli <data-folder>

This script is intended for manual verification and is not part of the FastAPI routes.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .standalone_tools import (
    DataProcessor,
    compute_stats,
    run_heavy_computation,
    send_email,
    write_output,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("run_tools_cli")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python -m api.utils.run_tools_cli <data-folder>")
        return 1

    folder = Path(argv[1])
    dp = DataProcessor(folder)
    dp.load()

    try:
        first = dp.next()
        print("First item:", first)
    except StopIteration:
        print("No items found")

    nums = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = compute_stats(nums)
    print("Stats:", stats)

    out = folder / "out.txt"
    write_output(out, str(stats))

    send_email(None, "Report", "Processing complete")

    total = run_heavy_computation(1000)
    print("Total:", total)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
