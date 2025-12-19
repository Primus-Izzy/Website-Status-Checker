"""Pydantic schemas for API requests and responses"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingConfig(BaseModel):
    """Configuration for processing a job"""
    batch_size: int = Field(default=1000, ge=1, le=10000)
    concurrent: int = Field(default=100, ge=1, le=1000)
    timeout: int = Field(default=10, ge=1, le=60)
    retry_count: int = Field(default=2, ge=0, le=5)
    url_column: str = Field(default="url")
    include_inactive: bool = Field(default=True)
    include_errors: bool = Field(default=False)


class JobProgress(BaseModel):
    """Real-time job progress information"""
    job_id: str
    status: JobStatus
    total_urls: int = 0
    processed_urls: int = 0
    active_count: int = 0
    inactive_count: int = 0
    error_count: int = 0
    current_batch: int = 0
    total_batches: int = 0
    processing_rate: float = 0.0
    eta_seconds: float = 0.0
    start_time: datetime
    errors: List[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response after file upload"""
    job_id: str
    filename: str
    size: int
    url_count: Optional[int] = None


class ProcessingResponse(BaseModel):
    """Response when starting processing"""
    status: str
    job_id: str
    message: str = ""


class ResultsResponse(BaseModel):
    """Paginated results response"""
    job_id: str
    total_count: int
    page: int
    limit: int
    total_pages: int
    results: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    """Statistics for charts and visualization"""
    job_id: str
    active_count: int
    inactive_count: int
    error_count: int
    timeout_count: int
    invalid_url_count: int
    error_breakdown: Dict[str, int]
    response_time_avg: float
    response_time_min: float
    response_time_max: float
    processing_rate: float
