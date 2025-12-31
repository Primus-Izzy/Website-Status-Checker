#!/usr/bin/env python3
"""
Website Status Checker - FastAPI Web GUI

Main application entry point for the web interface.
"""

import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path

from gui.config import get_settings
from gui.middleware import setup_rate_limiting
from gui.middleware.logging import setup_request_logging
from gui.middleware.metrics import setup_metrics
from gui.services.file_handler import FileHandler
from gui.database.session import init_db, close_db
from src.utils.logging_config import setup_logging, get_logger
from src.utils.error_tracking import initialize_error_tracking

# Get settings
settings = get_settings()

# Setup structured logging
setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    log_file=settings.log_file if settings.log_file else None,
    enable_console=True
)
logger = get_logger(__name__)

# Initialize error tracking if enabled
if settings.enable_error_tracking:
    try:
        initialize_error_tracking(
            enable_sentry=bool(settings.sentry_dsn),
            sentry_dsn=settings.sentry_dsn if settings.sentry_dsn else None,
            environment=settings.sentry_environment or settings.env,
            release=settings.app_version
        )
        logger.info("Error tracking initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize error tracking: {e}")

# Validate production configuration
if settings.is_production:
    config_issues = settings.validate_production_config()
    if config_issues:
        logger.error("Production configuration issues detected:")
        for issue in config_issues:
            logger.error(f"  - {issue}")
        if any("CRITICAL" in issue for issue in config_issues):
            raise RuntimeError("Critical configuration issues must be fixed before production deployment")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="High-performance website status validation with real-time monitoring",
    docs_url="/api/docs" if not settings.is_production else None,  # Disable docs in production
    redoc_url="/api/redoc" if not settings.is_production else None,
    debug=settings.debug
)

# Configure CORS with environment-based settings
cors_config = settings.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

logger.info(f"CORS configured with allowed origins: {cors_config['allow_origins']}")

# Setup rate limiting
setup_rate_limiting(app)

# Setup request logging middleware
setup_request_logging(
    app,
    exclude_paths=["/health", "/health/live", "/health/ready", "/metrics", "/static"],
    log_request_body=False,  # Don't log request bodies in production
    log_response_body=False,  # Don't log response bodies
    enable_performance_logging=True,
    slow_request_threshold_ms=1000
)

# Setup Prometheus metrics if enabled
if settings.enable_metrics:
    setup_metrics(
        app,
        app_name=settings.app_name,
        app_version=settings.app_version,
        environment=settings.env
    )
    logger.info("Prometheus metrics enabled")

# Add request size limit middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Middleware to enforce upload size limits."""
    if request.method == "POST" and "/upload" in request.url.path:
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > settings.max_upload_size_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"File too large. Maximum size is {settings.max_upload_size_mb}MB"
                    }
                )
    response = await call_next(request)
    return response

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API routers
from gui.api import upload, process, results, stats, sse, health, metrics, admin

app.include_router(health.router, tags=["health"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(sse.router, prefix="/api/sse", tags=["sse"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

# Include metrics router if enabled
if settings.enable_metrics:
    app.include_router(metrics.router, tags=["metrics"])


@app.get("/")
async def index(request: Request):
    """Render main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.env
    }


async def cleanup_old_files_task():
    """Background task to periodically clean up old files."""
    file_handler = FileHandler()

    logger.info(f"File cleanup task started (retention: {settings.job_retention_hours} hours)")

    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            logger.debug("Running file cleanup task...")
            await file_handler.cleanup_old_files(max_age_hours=settings.job_retention_hours)
            logger.debug("File cleanup task completed")
        except asyncio.CancelledError:
            logger.info("File cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in file cleanup task: {e}", exc_info=True)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.env}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"SSL verification default: {settings.ssl_verify_default}")
    logger.info(f"Rate limiting: {'enabled' if settings.rate_limit_enabled else 'disabled'}")
    logger.info(f"Max upload size: {settings.max_upload_size_mb}MB")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        if settings.is_production:
            raise RuntimeError("Database initialization required for production") from e

    # Start background file cleanup task
    asyncio.create_task(cleanup_old_files_task())
    logger.info("Background file cleanup task started")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down application")

    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
