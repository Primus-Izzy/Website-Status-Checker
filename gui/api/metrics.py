"""
Metrics API Endpoints

Provides Prometheus-compatible metrics endpoint for monitoring.
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from gui.middleware.metrics import update_system_metrics

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.

    Example metrics:
        # HELP http_requests_total Total HTTP requests
        # TYPE http_requests_total counter
        http_requests_total{method="GET",endpoint="/api/upload",status_code="200"} 42.0

        # HELP http_request_duration_seconds HTTP request duration in seconds
        # TYPE http_request_duration_seconds histogram
        http_request_duration_seconds_bucket{method="GET",endpoint="/api/upload",le="0.1"} 35.0
        http_request_duration_seconds_bucket{method="GET",endpoint="/api/upload",le="0.5"} 40.0
        http_request_duration_seconds_sum{method="GET",endpoint="/api/upload"} 12.5
        http_request_duration_seconds_count{method="GET",endpoint="/api/upload"} 42.0

    Returns:
        Prometheus metrics in text format
    """
    # Update system metrics before returning
    update_system_metrics()

    # Generate Prometheus metrics output
    metrics_output = generate_latest()

    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/summary")
async def metrics_summary():
    """
    Human-readable metrics summary.

    Returns a JSON summary of key metrics for dashboards and monitoring.

    Returns:
        JSON object with metric summaries
    """
    from gui.middleware.metrics import (
        http_requests_total,
        urls_checked_total,
        batch_processing_total,
        file_uploads_total,
        errors_total,
        active_jobs
    )
    from prometheus_client import REGISTRY

    # Collect current values
    summary = {
        "http": {
            "total_requests": sum(
                sample.value
                for metric in REGISTRY.collect()
                if metric.name == "http_requests_total"
                for sample in metric.samples
            ),
        },
        "urls": {
            "total_checked": sum(
                sample.value
                for metric in REGISTRY.collect()
                if metric.name == "urls_checked_total"
                for sample in metric.samples
            ),
        },
        "batch": {
            "total_jobs": sum(
                sample.value
                for metric in REGISTRY.collect()
                if metric.name == "batch_processing_total"
                for sample in metric.samples
            ),
            "active_jobs": active_jobs._value._value if hasattr(active_jobs, '_value') else 0,
        },
        "uploads": {
            "total_uploads": sum(
                sample.value
                for metric in REGISTRY.collect()
                if metric.name == "file_uploads_total"
                for sample in metric.samples
            ),
        },
        "errors": {
            "total_errors": sum(
                sample.value
                for metric in REGISTRY.collect()
                if metric.name == "errors_total"
                for sample in metric.samples
            ),
        },
    }

    return summary
