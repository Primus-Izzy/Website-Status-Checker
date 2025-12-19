"""File Handler - Manages file uploads and storage"""

import aiofiles
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
import pandas as pd


class FileHandler:
    """Handles file uploads, validation, and storage"""

    def __init__(self, upload_dir: str = "gui/uploads", export_dir: str = "gui/exports"):
        self.upload_dir = Path(upload_dir)
        self.export_dir = Path(export_dir)

        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> Tuple[str, Path, int]:
        """
        Save uploaded file and return job ID, file path, and URL count.

        Args:
            file: Uploaded file

        Returns:
            Tuple of (job_id, file_path, url_count)
        """
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Get file extension
        file_ext = Path(file.filename).suffix.lower()

        # Save file
        file_path = self.upload_dir / f"{job_id}{file_ext}"

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Count URLs
        url_count = await self._count_urls(file_path)

        return job_id, file_path, url_count

    async def _count_urls(self, file_path: Path) -> int:
        """
        Count total URLs in file.

        Args:
            file_path: Path to uploaded file

        Returns:
            Number of URLs
        """
        try:
            file_ext = file_path.suffix.lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                # Text file
                async with aiofiles.open(file_path, 'r') as f:
                    lines = await f.readlines()
                return sum(1 for line in lines if line.strip())

            # Return row count
            return len(df)

        except Exception:
            return 0

    def get_upload_path(self, job_id: str) -> Path:
        """
        Get file path for a job ID.

        Args:
            job_id: Job identifier

        Returns:
            Path to uploaded file
        """
        # Find file with job_id prefix
        for file_path in self.upload_dir.glob(f"{job_id}.*"):
            return file_path

        raise FileNotFoundError(f"No upload found for job {job_id}")

    def get_export_path(self, job_id: str, format: str = "csv") -> Path:
        """
        Get export file path for a job.

        Args:
            job_id: Job identifier
            format: Export format (csv, json, xlsx)

        Returns:
            Path for export file
        """
        return self.export_dir / f"{job_id}_results.{format}"

    async def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Remove old upload and export files.

        Args:
            max_age_hours: Maximum file age in hours
        """
        import time

        max_age_seconds = max_age_hours * 3600
        current_time = time.time()

        for directory in [self.upload_dir, self.export_dir]:
            for file_path in directory.glob("*"):
                if file_path.is_file() and file_path.name != ".gitkeep":
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
