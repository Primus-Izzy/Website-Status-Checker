"""
Health Check API Endpoints

Provides detailed health check information for monitoring and orchestration.
"""

import psutil
import time
import logging
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
from sqlalchemy import text

from gui.config import get_settings
from gui.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Store application start time
app_start_time = time.time()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str
    uptime_seconds: float
    checks: Dict[str, Any]


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    version: str
    environment: str
    uptime_seconds: float
    system: Dict[str, Any]
    application: Dict[str, Any]
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Basic health check endpoint.

    Returns basic health status and uptime. Suitable for load balancer health checks.

    Returns:
        HealthResponse with health status
    """
    uptime = time.time() - app_start_time

    # Run health checks
    db_check = await check_database()

    checks = {
        "api": "ok",
        "database": db_check,
        "uploads_dir": check_directory(settings.upload_dir),
        "exports_dir": check_directory(settings.export_dir),
    }

    # Determine overall status
    all_ok = all(v == "ok" for v in checks.values())
    overall_status = "healthy" if all_ok else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.env,
        uptime_seconds=uptime,
        checks=checks
    )


@router.get("/health/ready", tags=["health"])
async def readiness_check(response: Response):
    """
    Kubernetes readiness probe endpoint.

    Checks if the application is ready to accept traffic.

    Returns:
        200 if ready, 503 if not ready
    """
    try:
        # Check critical dependencies
        upload_dir_ok = check_directory(settings.upload_dir) == "ok"
        export_dir_ok = check_directory(settings.export_dir) == "ok"

        if upload_dir_ok and export_dir_ok:
            return {"status": "ready"}
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "not_ready", "reason": "directories_not_accessible"}

    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": str(e)}


@router.get("/health/live", tags=["health"])
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Simple check that the application is running.

    Returns:
        200 if alive
    """
    return {"status": "alive"}


@router.get("/health/detailed", response_model=DetailedHealthResponse, tags=["health"])
async def detailed_health_check():
    """
    Detailed health check with system metrics.

    Provides comprehensive health information including system resources,
    application metrics, and dependency status.

    Returns:
        DetailedHealthResponse with comprehensive health data
    """
    uptime = time.time() - app_start_time

    # System metrics
    system_info = {
        "cpu": {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=0.1),
        },
        "memory": {
            "total_mb": psutil.virtual_memory().total / (1024 ** 2),
            "available_mb": psutil.virtual_memory().available / (1024 ** 2),
            "percent_used": psutil.virtual_memory().percent,
        },
        "disk": {
            "total_gb": psutil.disk_usage('/').total / (1024 ** 3),
            "free_gb": psutil.disk_usage('/').free / (1024 ** 3),
            "percent_used": psutil.disk_usage('/').percent,
        }
    }

    # Application metrics
    app_info = {
        "uptime_seconds": uptime,
        "uptime_human": format_uptime(uptime),
        "version": settings.app_version,
        "environment": settings.env,
        "debug_mode": settings.debug,
        "ssl_verification": settings.ssl_verify_default,
        "rate_limiting": settings.rate_limit_enabled,
        "max_upload_mb": settings.max_upload_size_mb,
    }

    # Health checks
    db_check = await check_database()

    checks = {
        "api": "ok",
        "database": db_check,
        "uploads_dir": check_directory(settings.upload_dir),
        "exports_dir": check_directory(settings.export_dir),
        "memory": check_memory(),
        "disk": check_disk(),
    }

    # Determine overall status
    critical_checks = ["api", "database", "uploads_dir", "exports_dir"]
    critical_ok = all(checks[k] == "ok" for k in critical_checks)
    all_ok = all(v == "ok" for v in checks.values())

    if critical_ok and all_ok:
        overall_status = "healthy"
    elif critical_ok:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return DetailedHealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.env,
        uptime_seconds=uptime,
        system=system_info,
        application=app_info,
        checks=checks
    )


def check_directory(dir_path: str) -> str:
    """
    Check if directory exists and is writable.

    Args:
        dir_path: Directory path to check

    Returns:
        "ok" if directory is accessible, error message otherwise
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        # Try to create a test file
        test_file = path / ".health_check"
        test_file.touch()
        test_file.unlink()

        return "ok"
    except Exception as e:
        return f"error: {str(e)}"


def check_memory() -> str:
    """
    Check memory usage.

    Returns:
        "ok" if memory usage is acceptable, warning otherwise
    """
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        return f"critical: {memory.percent:.1f}% used"
    elif memory.percent > 75:
        return f"warning: {memory.percent:.1f}% used"
    else:
        return "ok"


def check_disk() -> str:
    """
    Check disk usage.

    Returns:
        "ok" if disk usage is acceptable, warning otherwise
    """
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        return f"critical: {disk.percent:.1f}% used"
    elif disk.percent > 75:
        return f"warning: {disk.percent:.1f}% used"
    else:
        return "ok"


async def check_database() -> str:
    """
    Check database connectivity.

    Returns:
        "ok" if database is accessible, error message otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Execute a simple query to verify connectivity
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return f"error: {str(e)[:100]}"


def format_uptime(seconds: float) -> str:
    """
    Format uptime in human-readable format.

    Args:
        seconds: Uptime in seconds

    Returns:
        Formatted uptime string

    Example:
        >>> format_uptime(3665)
        '1h 1m 5s'
    """
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)
