"""
Database Models for Job and Result Persistence

Defines SQLAlchemy models for storing jobs, results, and related data.
Supports both SQLite (development) and PostgreSQL (production).
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class URLStatus(str, enum.Enum):
    """URL check status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TIMEOUT = "timeout"


class Job(Base):
    """
    Job model for tracking batch processing jobs.

    Stores metadata about file uploads and processing jobs,
    including status, statistics, and timestamps.
    """
    __tablename__ = "jobs"

    # Primary key
    id = Column(String(36), primary_key=True)  # UUID

    # Job metadata
    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)  # Bytes
    file_type = Column(String(10), nullable=False)  # csv, xlsx, txt

    # Processing status
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)

    # Processing configuration
    batch_size = Column(Integer, default=1000)
    max_concurrent = Column(Integer, default=100)
    timeout = Column(Integer, default=10)
    retry_count = Column(Integer, default=2)
    verify_ssl = Column(Boolean, default=True)

    # Statistics
    total_urls = Column(Integer, default=0)
    processed_urls = Column(Integer, default=0)
    active_urls = Column(Integer, default=0)
    inactive_urls = Column(Integer, default=0)
    error_urls = Column(Integer, default=0)

    # Timing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Duration (seconds)
    duration = Column(Float, nullable=True)

    # Error information
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Results
    output_file = Column(String(255), nullable=True)
    output_format = Column(String(10), nullable=True)  # csv, json, xlsx

    # User context
    client_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(255), nullable=True)

    # Relationships
    results = relationship("URLCheckResult", back_populates="job", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_job_status_created', 'status', 'created_at'),
        Index('idx_job_completed', 'completed_at'),
    )

    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, filename={self.filename})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate processing progress percentage."""
        if self.total_urls == 0:
            return 0.0
        return (self.processed_urls / self.total_urls) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate (active URLs / processed URLs)."""
        if self.processed_urls == 0:
            return 0.0
        return (self.active_urls / self.processed_urls) * 100

    @property
    def is_active(self) -> bool:
        """Check if job is currently active."""
        return self.status in [JobStatus.PENDING, JobStatus.PROCESSING]

    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]


class URLCheckResult(Base):
    """
    URL check result model.

    Stores individual URL check results including status,
    response times, and error information.
    """
    __tablename__ = "url_check_results"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to job
    job_id = Column(String(36), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)

    # URL information
    url = Column(String(2048), nullable=False)  # Max URL length
    normalized_url = Column(String(2048), nullable=True, index=True)

    # Check result
    status = Column(Enum(URLStatus), nullable=False, index=True)
    status_code = Column(Integer, nullable=True)

    # Timing
    response_time = Column(Float, nullable=True)  # Seconds
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Response information
    content_type = Column(String(100), nullable=True)
    content_length = Column(Integer, nullable=True)
    final_url = Column(String(2048), nullable=True)  # After redirects
    redirect_count = Column(Integer, default=0)

    # Error information
    error_message = Column(Text, nullable=True)
    error_category = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)

    # SSL information
    ssl_verified = Column(Boolean, nullable=True)
    ssl_error = Column(Text, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="results")

    # Indexes
    __table_args__ = (
        Index('idx_result_job_status', 'job_id', 'status'),
        Index('idx_result_checked', 'checked_at'),
        Index('idx_result_url', 'url', mysql_length=255),  # Limit index length for MySQL
    )

    def __repr__(self):
        return f"<URLCheckResult(id={self.id}, url={self.url[:50]}, status={self.status})>"

    @property
    def is_successful(self) -> bool:
        """Check if URL check was successful."""
        return self.status == URLStatus.ACTIVE and 200 <= (self.status_code or 0) < 400

    @property
    def has_error(self) -> bool:
        """Check if URL check had an error."""
        return self.status in [URLStatus.ERROR, URLStatus.TIMEOUT]


class ProcessingLog(Base):
    """
    Processing log for audit trail.

    Stores detailed logs of processing events for debugging
    and audit purposes.
    """
    __tablename__ = "processing_logs"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to job
    job_id = Column(String(36), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)

    # Log information
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Context
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)

    # Additional data (JSON)
    extra_data = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_log_job_time', 'job_id', 'timestamp'),
        Index('idx_log_level', 'level'),
    )

    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, level={self.level}, message={self.message[:50]})>"


class SystemMetric(Base):
    """
    System metrics for monitoring and performance tracking.

    Stores periodic snapshots of system metrics for historical
    analysis and capacity planning.
    """
    __tablename__ = "system_metrics"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # CPU metrics
    cpu_percent = Column(Float, nullable=True)
    cpu_count = Column(Integer, nullable=True)

    # Memory metrics
    memory_total = Column(Integer, nullable=True)  # Bytes
    memory_available = Column(Integer, nullable=True)  # Bytes
    memory_percent = Column(Float, nullable=True)

    # Disk metrics
    disk_total = Column(Integer, nullable=True)  # Bytes
    disk_free = Column(Integer, nullable=True)  # Bytes
    disk_percent = Column(Float, nullable=True)

    # Application metrics
    active_jobs = Column(Integer, default=0)
    total_jobs = Column(Integer, default=0)
    urls_per_second = Column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_metric_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<SystemMetric(timestamp={self.timestamp}, cpu={self.cpu_percent}%, mem={self.memory_percent}%)>"


class APIKey(Base):
    """
    API Key model for authentication.

    Stores API keys for accessing the web API with rate limiting
    and usage tracking.
    """
    __tablename__ = "api_keys"

    # Primary key
    id = Column(Integer, primary_key=True)

    # API Key (hashed for security)
    key_hash = Column(String(128), unique=True, nullable=False, index=True)
    key_prefix = Column(String(8), nullable=False)  # First 8 chars for identification

    # Key metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Rate limiting
    rate_limit_per_hour = Column(Integer, default=1000)
    rate_limit_per_minute = Column(Integer, default=100)

    # Usage tracking
    total_requests = Column(Integer, default=0)

    # Optional: User/owner association
    owner_email = Column(String(255), nullable=True)
    owner_name = Column(String(255), nullable=True)

    # IP whitelist (comma-separated)
    ip_whitelist = Column(Text, nullable=True)

    # Scopes/permissions (comma-separated)
    scopes = Column(String(500), default="read,write")

    # Indexes
    __table_args__ = (
        Index('idx_apikey_active', 'is_active'),
        Index('idx_apikey_created', 'created_at'),
    )

    def __repr__(self):
        return f"<APIKey(name={self.name}, prefix={self.key_prefix}, active={self.is_active})>"

    def is_expired(self) -> bool:
        """Check if API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if API key has a specific scope."""
        if not self.scopes:
            return False
        return scope in self.scopes.split(',')


# Helper functions for model creation and queries

def create_job(
    job_id: str,
    filename: str,
    file_size: int,
    file_type: str,
    **kwargs
) -> Job:
    """
    Create a new job instance.

    Args:
        job_id: Unique job identifier (UUID)
        filename: Original filename
        file_size: File size in bytes
        file_type: File extension (csv, xlsx, txt)
        **kwargs: Additional job attributes

    Returns:
        Job instance (not saved to database)
    """
    return Job(
        id=job_id,
        filename=filename,
        file_size=file_size,
        file_type=file_type,
        **kwargs
    )


def create_url_result(
    job_id: str,
    url: str,
    status: URLStatus,
    **kwargs
) -> URLCheckResult:
    """
    Create a new URL check result instance.

    Args:
        job_id: Job identifier
        url: URL that was checked
        status: Check status
        **kwargs: Additional result attributes

    Returns:
        URLCheckResult instance (not saved to database)
    """
    return URLCheckResult(
        job_id=job_id,
        url=url,
        status=status,
        **kwargs
    )


def create_processing_log(
    job_id: str,
    level: str,
    message: str,
    **kwargs
) -> ProcessingLog:
    """
    Create a new processing log entry.

    Args:
        job_id: Job identifier
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **kwargs: Additional log attributes

    Returns:
        ProcessingLog instance (not saved to database)
    """
    return ProcessingLog(
        job_id=job_id,
        level=level,
        message=message,
        **kwargs
    )
