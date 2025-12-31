"""File Upload API Endpoint"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from gui.services.file_handler import FileHandler
from gui.services.job_manager import JobManager
from gui.models.schemas import UploadResponse
from gui.config import get_settings
from gui.middleware import upload_rate_limit, limiter

router = APIRouter()
file_handler = FileHandler()
job_manager = JobManager()
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("/", response_model=UploadResponse)
@limiter.limit(f"{settings.rate_limit_uploads_per_minute}/minute")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Upload a CSV or Excel file for processing.

    Args:
        file: Uploaded file (CSV, XLSX, XLS)

    Returns:
        UploadResponse with job_id and file info

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file size (if available from client)
    if file.size and file.size > settings.max_upload_size_bytes:
        logger.warning(f"Upload rejected: file too large ({file.size} bytes)")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB"
        )

    # Validate file type
    allowed_types = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/csv'
    ]

    if file.content_type not in allowed_types:
        logger.warning(f"Upload rejected: invalid content type {file.content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: CSV, XLSX. Got: {file.content_type}"
        )

    # Validate file extension
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = file.filename.split('.')[-1].lower() if file.filename else ''
    if f'.{file_ext}' not in allowed_extensions:
        logger.warning(f"Upload rejected: invalid file extension .{file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        logger.info(f"Processing upload: {file.filename} ({file.size or 0} bytes)")

        # Save file and get job ID
        job_id, file_path, url_count = await file_handler.save_upload(file)

        # Create job in job manager
        await job_manager.create_job(job_id, url_count)

        logger.info(f"Upload successful: job_id={job_id}, urls={url_count}")

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            size=file.size or 0,
            url_count=url_count
        )

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upload: {str(e)}"
        )
