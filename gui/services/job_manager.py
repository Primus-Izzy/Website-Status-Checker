"""Job Manager - Tracks and manages processing jobs"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import time

from gui.models.schemas import JobStatus, JobProgress


class JobManager:
    """
    Manages all active processing jobs with progress tracking.

    Provides thread-safe access to job status and progress information
    for real-time updates via Server-Sent Events.
    """

    def __init__(self):
        self.jobs: Dict[str, JobProgress] = {}
        self.progress_queues: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, job_id: str, total_urls: int) -> JobProgress:
        """
        Create a new job for tracking.

        Args:
            job_id: Unique job identifier
            total_urls: Total number of URLs to process

        Returns:
            JobProgress object
        """
        async with self._lock:
            job = JobProgress(
                job_id=job_id,
                status=JobStatus.PENDING,
                total_urls=total_urls,
                processed_urls=0,
                active_count=0,
                inactive_count=0,
                error_count=0,
                current_batch=0,
                total_batches=0,
                processing_rate=0.0,
                eta_seconds=0.0,
                start_time=datetime.now(),
                errors=[]
            )
            self.jobs[job_id] = job
            self.progress_queues[job_id] = asyncio.Queue()
            return job

    async def update_progress(
        self,
        job_id: str,
        **kwargs
    ) -> None:
        """
        Update job progress with new values.

        Args:
            job_id: Job identifier
            **kwargs: Fields to update (status, processed_urls, active_count, etc.)
        """
        async with self._lock:
            if job_id not in self.jobs:
                return

            job = self.jobs[job_id]

            # Update fields
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            # Calculate processing rate and ETA
            if job.status == JobStatus.PROCESSING:
                elapsed = (datetime.now() - job.start_time).total_seconds()
                if elapsed > 0 and job.processed_urls > 0:
                    job.processing_rate = job.processed_urls / elapsed

                    if job.processing_rate > 0:
                        remaining = job.total_urls - job.processed_urls
                        job.eta_seconds = remaining / job.processing_rate

            # Notify SSE listeners
            try:
                self.progress_queues[job_id].put_nowait(job)
            except asyncio.QueueFull:
                pass  # Queue full, skip this update

    async def get_progress(self, job_id: str, timeout: float = 30.0) -> Optional[JobProgress]:
        """
        Get current progress for a job (blocking until update available).

        Used by SSE endpoints to stream updates.

        Args:
            job_id: Job identifier
            timeout: Maximum wait time in seconds

        Returns:
            JobProgress object or None if timeout
        """
        if job_id not in self.progress_queues:
            return None

        try:
            job = await asyncio.wait_for(
                self.progress_queues[job_id].get(),
                timeout=timeout
            )
            return job
        except asyncio.TimeoutError:
            # Return current state on timeout
            return self.jobs.get(job_id)

    async def get_job(self, job_id: str) -> Optional[JobProgress]:
        """
        Get current job state (non-blocking).

        Args:
            job_id: Job identifier

        Returns:
            JobProgress object or None
        """
        return self.jobs.get(job_id)

    async def add_error(self, job_id: str, error_message: str) -> None:
        """
        Add an error message to the job.

        Args:
            job_id: Job identifier
            error_message: Error description
        """
        async with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].errors.append(error_message)

    async def cleanup_job(self, job_id: str, keep_history: bool = True) -> None:
        """
        Clean up job resources.

        Args:
            job_id: Job identifier
            keep_history: If True, keep job data but remove queue
        """
        async with self._lock:
            if job_id in self.progress_queues:
                del self.progress_queues[job_id]

            if not keep_history and job_id in self.jobs:
                del self.jobs[job_id]

    def list_jobs(self) -> Dict[str, JobProgress]:
        """
        Get all current jobs.

        Returns:
            Dictionary of job_id -> JobProgress
        """
        return self.jobs.copy()
