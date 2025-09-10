from __future__ import annotations

from pathlib import Path
from typing import Iterable

from fastapi import UploadFile

from ..utils.settings import get_settings


class StorageService:
    """
    Service to manage file storage for uploads, outputs, reports, and visualization.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.UPLOAD_DIR)
        self.output_dir = Path(self.settings.OUTPUT_DIR)
        self.reports_dir = Path(self.settings.REPORTS_DIR)
        self.viz_dir = Path(self.settings.VIZ_DIR)

        for p in [self.upload_dir, self.output_dir, self.reports_dir, self.viz_dir]:
            p.mkdir(parents=True, exist_ok=True)

    # PUBLIC_INTERFACE
    async def save_upload(self, file: UploadFile) -> Path:
        """
        Save an uploaded file to the uploads directory.
        """
        dest = self.upload_dir / file.filename
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        await file.close()
        return dest

    # PUBLIC_INTERFACE
    def list_uploads(self) -> Iterable[Path]:
        """
        List files in the uploads directory.
        """
        return sorted(self.upload_dir.glob("*"))

    # PUBLIC_INTERFACE
    def get_upload_path(self, filename: str) -> Path:
        """
        Get absolute path to a file in uploads.
        """
        return self.upload_dir / filename

    # PUBLIC_INTERFACE
    def get_output_path(self, stem: str, suffix: str) -> Path:
        """
        Construct a path for outputs directory, ensuring suffix starts with dot.
        """
        if not suffix.startswith("."):
            suffix = "." + suffix
        return self.output_dir / f"{stem}{suffix}"

    # PUBLIC_INTERFACE
    def get_report_path(self, stem: str, suffix: str) -> Path:
        """
        Construct a path for reports directory.
        """
        if not suffix.startswith("."):
            suffix = "." + suffix
        return self.reports_dir / f"{stem}{suffix}"

    # PUBLIC_INTERFACE
    def get_viz_path(self, stem: str, suffix: str) -> Path:
        """
        Construct a path for visualization directory.
        """
        if not suffix.startswith("."):
            suffix = "." + suffix
        return self.viz_dir / f"{stem}{suffix}"
