"""Server-Sent Events API for real-time progress updates"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from gui.services.job_manager import JobManager
import json
import asyncio

router = APIRouter()
job_manager = JobManager()


@router.get("/progress/{job_id}")
async def stream_progress(job_id: str):
    """
    Stream real-time progress updates via Server-Sent Events.

    Args:
        job_id: Job identifier

    Returns:
        StreamingResponse with SSE events
    """
    async def event_generator():
        """Generate SSE events with job progress"""
        while True:
            # Get progress update (blocks until available or timeout)
            progress = await job_manager.get_progress(job_id, timeout=1.0)

            if not progress:
                # Job not found
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            # Convert to dict for JSON serialization
            progress_dict = {
                "job_id": progress.job_id,
                "status": progress.status.value,
                "total_urls": progress.total_urls,
                "processed_urls": progress.processed_urls,
                "active_count": progress.active_count,
                "inactive_count": progress.inactive_count,
                "error_count": progress.error_count,
                "current_batch": progress.current_batch,
                "total_batches": progress.total_batches,
                "processing_rate": progress.processing_rate,
                "eta_seconds": progress.eta_seconds,
                "start_time": progress.start_time.isoformat(),
                "errors": progress.errors
            }

            # Send progress update
            yield f"data: {json.dumps(progress_dict)}\n\n"

            # Check if job is complete
            if progress.status.value in ['completed', 'failed']:
                break

            await asyncio.sleep(0.1)  # Small delay between updates

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
