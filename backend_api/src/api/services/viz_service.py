from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Optional, Tuple

from ..utils.errors import AppException
from .storage_service import StorageService


class VisualizationService:
    """
    Service to generate simple SVG visualizations without external plotting libraries.
    Supports histogram and boxplot for a single numeric column.
    The images are saved as .svg files in the viz directory.
    """

    def __init__(self, storage: StorageService) -> None:
        self.storage = storage

    def _detect_format(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".csv":
            return "csv"
        if ext in (".jsonl", ".ndjson"):
            return "jsonl"
        raise AppException("Unsupported file format. Use CSV or JSONL.")

    def _load_numeric_column(self, path: Path, column: str) -> List[float]:
        fmt = self._detect_format(path)
        values: List[float] = []
        if fmt == "csv":
            with path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        v = float(row.get(column)) if row.get(column) not in (None, "") else None
                    except (TypeError, ValueError):
                        v = None
                    if v is not None:
                        values.append(v)
        else:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    try:
                        v = float(obj.get(column)) if obj.get(column) not in (None, "") else None
                    except (TypeError, ValueError):
                        v = None
                    if v is not None:
                        values.append(v)
        return values

    def _histogram(self, values: List[float], bins: int) -> Tuple[List[float], List[int]]:
        if not values:
            return [], []
        mn, mx = min(values), max(values)
        if mn == mx:
            # Single bin case
            return [mn, mx], [len(values)]
        width = (mx - mn) / bins
        edges = [mn + i * width for i in range(bins + 1)]
        counts = [0] * bins
        for v in values:
            idx = min(int((v - mn) / width), bins - 1)
            counts[idx] += 1
        return edges, counts

    def _boxplot_stats(self, values: List[float]) -> Tuple[float, float, float, float, float]:
        vs = sorted(values)
        n = len(vs)
        if n == 0:
            return 0, 0, 0, 0, 0
        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = int(k)
            c = min(f + 1, n - 1)
            if f == c:
                return vs[f]
            return vs[f] + (vs[c] - vs[f]) * (k - f)
        q1 = percentile(0.25)
        q2 = percentile(0.5)
        q3 = percentile(0.75)
        return vs[0], q1, q2, q3, vs[-1]

    def _render_svg_hist(self, edges: List[float], counts: List[int], width: int = 640, height: int = 360) -> str:
        padding = 40
        max_count = max(counts) if counts else 1
        bin_width = (width - 2 * padding) / max(1, len(counts))
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')
        for i, c in enumerate(counts):
            bar_h = 0 if max_count == 0 else (c / max_count) * (height - 2 * padding)
            x = padding + i * bin_width
            y = height - padding - bar_h
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bin_width - 2:.1f}" height="{bar_h:.1f}" fill="#4a90e2"/>')
        # axes
        svg.append(f'<line x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}" stroke="#333"/>')
        svg.append(f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" stroke="#333"/>')
        svg.append("</svg>")
        return "\n".join(svg)

    def _render_svg_box(self, stats: Tuple[float, float, float, float, float], width: int = 640, height: int = 360) -> str:
        padding = 60
        mn, q1, q2, q3, mx = stats
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
        svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>')
        mid_y = height / 2
        scale = (width - 2 * padding) / (mx - mn) if mx > mn else 1.0
        def sx(v: float) -> float:
            return padding + (v - mn) * scale
        # whiskers
        svg.append(f'<line x1="{sx(mn):.1f}" y1="{mid_y:.1f}" x2="{sx(mx):.1f}" y2="{mid_y:.1f}" stroke="#333"/>')
        # box
        box_y = mid_y - 40
        box_h = 80
        svg.append(f'<rect x="{sx(q1):.1f}" y="{box_y:.1f}" width="{max(2.0, sx(q3)-sx(q1)):.1f}" height="{box_h}" fill="#e9f2fd" stroke="#4a90e2"/>')
        # median
        svg.append(f'<line x1="{sx(q2):.1f}" y1="{box_y:.1f}" x2="{sx(q2):.1f}" y2="{box_y+box_h:.1f}" stroke="#e24a4a"/>')
        svg.append("</svg>")
        return "\n".join(svg)

    # PUBLIC_INTERFACE
    def generate_plot(self, filename: str, column: str, kind: str = "hist", bins: Optional[int] = 20) -> Path:
        """
        Generate a simple SVG plot for the given column. Returns the saved file path.
        """
        src = self.storage.get_upload_path(filename)
        if not src.exists():
            raise FileNotFoundError(filename)
        values = self._load_numeric_column(src, column)
        if not values:
            raise ValueError("No numeric values found for the specified column.")

        stem = Path(filename).stem
        out = self.storage.get_viz_path(f"{stem}_{column}_{kind}", ".svg")

        if kind == "hist":
            b = bins or 20
            edges, counts = self._histogram(values, b)
            svg = self._render_svg_hist(edges, counts)
        elif kind == "box":
            stats = self._boxplot_stats(values)
            svg = self._render_svg_box(stats)
        else:
            raise ValueError("Unsupported plot kind. Use 'hist' or 'box'.")

        out.write_text(svg, encoding="utf-8")
        return out
