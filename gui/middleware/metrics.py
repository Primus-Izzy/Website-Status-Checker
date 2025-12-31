"""
Prometheus Metrics Middleware for FastAPI

Provides comprehensive metrics collection for monitoring and observability:
- HTTP request metrics (count, duration, size)
- Business metrics (URLs checked, success rate)
- System metrics (memory, CPU)
- Custom application metrics
"""

import time
import psutil
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
    REGISTRY
)
from prometheus_client.core import CollectorRegistry as CoreCollectorRegistry


# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Application Info
app_info = Info(
    'app',
    'Application information'
)

# Business Metrics
urls_checked_total = Counter(
    'urls_checked_total',
    'Total number of URLs checked',
    ['status_result']
)

urls_check_duration_seconds = Histogram(
    'urls_check_duration_seconds',
    'URL check duration in seconds',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

batch_processing_total = Counter(
    'batch_processing_total',
    'Total number of batch processing jobs',
    ['status']
)

batch_processing_duration_seconds = Histogram(
    'batch_processing_duration_seconds',
    'Batch processing duration in seconds'
)

active_jobs = Gauge(
    'active_jobs',
    'Number of currently active processing jobs'
)

# File Upload Metrics
file_uploads_total = Counter(
    'file_uploads_total',
    'Total file uploads',
    ['status', 'file_type']
)

file_upload_size_bytes = Histogram(
    'file_upload_size_bytes',
    'File upload size in bytes',
    buckets=(1024, 10240, 102400, 1024000, 10240000, 102400000)  # 1KB to 100MB
)

# Error Metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'error_category']
)

# System Metrics
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

system_memory_available = Gauge(
    'system_memory_available_bytes',
    'System available memory in bytes'
)

process_memory_usage = Gauge(
    'process_memory_usage_bytes',
    'Process memory usage in bytes'
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for HTTP requests.

    Tracks:
    - Request count by method, endpoint, status code
    - Request duration
    - Request/response sizes
    - Active requests
    """

    def __init__(self, app, exclude_paths: list[str] = None):
        """
        Initialize metrics middleware.

        Args:
            app: FastAPI application
            exclude_paths: Paths to exclude from metrics (e.g., /metrics, /health)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/metrics", "/health/live"]

    def should_track_path(self, path: str) -> bool:
        """
        Check if path should be tracked.

        Args:
            path: Request path

        Returns:
            True if should track, False otherwise
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        return True

    def get_endpoint(self, path: str) -> str:
        """
        Get normalized endpoint name from path.

        Args:
            path: Request path

        Returns:
            Normalized endpoint name
        """
        # Normalize path to avoid high cardinality
        # Replace UUIDs and IDs with placeholders
        import re

        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{uuid}',
            path,
            flags=re.IGNORECASE
        )

        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)

        return path

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Skip excluded paths
        if not self.should_track_path(request.url.path):
            return await call_next(request)

        method = request.method
        endpoint = self.get_endpoint(request.url.path)

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Track request size
        request_size = int(request.headers.get("content-length", 0))
        if request_size > 0:
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Track response metrics
            duration = time.time() - start_time
            status_code = response.status_code

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Track response size
            response_size = int(response.headers.get("content-length", 0))
            if response_size > 0:
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)

            return response

        except Exception as exc:
            # Track error
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            raise

        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def update_system_metrics():
    """Update system resource metrics."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_usage.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.used)
        system_memory_available.set(memory.available)

        # Process memory
        process = psutil.Process()
        process_memory = process.memory_info().rss
        process_memory_usage.set(process_memory)

    except Exception:
        # Ignore errors in metrics collection
        pass


def setup_metrics(app, app_name: str, app_version: str, environment: str):
    """
    Set up Prometheus metrics collection.

    Args:
        app: FastAPI application
        app_name: Application name
        app_version: Application version
        environment: Environment (development, staging, production)
    """
    # Set application info
    app_info.info({
        'name': app_name,
        'version': app_version,
        'environment': environment
    })

    # Add metrics middleware
    app.add_middleware(
        PrometheusMetricsMiddleware,
        exclude_paths=["/metrics", "/health/live", "/static"]
    )

    # Update system metrics on startup
    update_system_metrics()


# Utility functions for business metrics

def track_url_check(status_result: str, duration_seconds: float):
    """
    Track URL check metrics.

    Args:
        status_result: Check result (ACTIVE, INACTIVE, ERROR, TIMEOUT)
        duration_seconds: Check duration in seconds
    """
    urls_checked_total.labels(status_result=status_result).inc()
    urls_check_duration_seconds.observe(duration_seconds)


def track_batch_processing(status: str, duration_seconds: float):
    """
    Track batch processing metrics.

    Args:
        status: Processing status (success, failure, cancelled)
        duration_seconds: Processing duration in seconds
    """
    batch_processing_total.labels(status=status).inc()
    batch_processing_duration_seconds.observe(duration_seconds)


def track_file_upload(status: str, file_type: str, size_bytes: int):
    """
    Track file upload metrics.

    Args:
        status: Upload status (success, failure)
        file_type: File extension (csv, xlsx, txt)
        size_bytes: File size in bytes
    """
    file_uploads_total.labels(status=status, file_type=file_type).inc()
    file_upload_size_bytes.observe(size_bytes)


def track_error(error_type: str, error_category: str):
    """
    Track error metrics.

    Args:
        error_type: Error type/class name
        error_category: Error category (network, validation, etc.)
    """
    errors_total.labels(error_type=error_type, error_category=error_category).inc()


def increment_active_jobs():
    """Increment active jobs counter."""
    active_jobs.inc()


def decrement_active_jobs():
    """Decrement active jobs counter."""
    active_jobs.dec()
