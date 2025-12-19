"""File Upload API Endpoint"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from gui.services.file_handler import FileHandler
from gui.services.job_manager import JobManager
from gui.models.schemas import UploadResponse

router = APIRouter()
file_handler = FileHandler()
job_manager = JobManager()


@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV or Excel file for processing.

    Args:
        file: Uploaded file (CSV, XLSX, XLS)

    Returns:
        UploadResponse with job_id and file info
    """
    # Validate file type
    allowed_types = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/csv'
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: CSV, XLSX. Got: {file.content_type}"
        )

    # Validate file extension
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = file.filename.split('.')[-1].lower()
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        # Save file and get job ID
        job_id, file_path, url_count = await file_handler.save_upload(file)

        # Create job in job manager
        await job_manager.create_job(job_id, url_count)

        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            size=file.size or 0,
            url_count=url_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upload: {str(e)}"
        )
