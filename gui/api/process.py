"""Processing API Endpoints"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from gui.services.job_manager import JobManager
from gui.services.file_handler import FileHandler
from gui.services.processor import ProcessorService
from gui.models.schemas import ProcessingConfig, ProcessingResponse, JobProgress

router = APIRouter()
job_manager = JobManager()
file_handler = FileHandler()
processor_service = ProcessorService(job_manager, file_handler)


@router.post("/start/{job_id}", response_model=ProcessingResponse)
async def start_processing(
    job_id: str,
    config: ProcessingConfig,
    background_tasks: BackgroundTasks
):
    """
    Start processing a job in the background.

    Args:
        job_id: Job identifier
        config: Processing configuration
        background_tasks: FastAPI background tasks

    Returns:
        ProcessingResponse with status
    """
    # Check if job exists
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Start processing in background
    background_tasks.add_task(processor_service.process_job, job_id, config)

    return ProcessingResponse(
        status="started",
        job_id=job_id,
        message="Processing started in background"
    )


@router.get("/status/{job_id}", response_model=JobProgress)
async def get_status(job_id: str):
    """
    Get current status of a job.

    Args:
        job_id: Job identifier

    Returns:
        JobProgress with current status
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/jobs")
async def list_jobs():
    """
    List all current jobs.

    Returns:
        Dictionary of all jobs
    """
    jobs = job_manager.list_jobs()
    return {"jobs": jobs}
