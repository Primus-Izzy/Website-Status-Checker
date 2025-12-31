"""
Error Tracking Middleware for FastAPI

Captures and tracks exceptions in HTTP requests, integrates with the
global error tracking system.
"""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from src.utils.error_tracking import (
    get_error_tracker,
    ErrorCategory,
    ErrorSeverity,
    categorize_exception,
    get_error_severity,
)


logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture and track HTTP request errors.

    Automatically categorizes exceptions, sends them to error tracking,
    and returns appropriate HTTP error responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and capture any errors.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response

        except StarletteHTTPException as exc:
            # HTTP exceptions are expected, just return them
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )

        except RequestValidationError as exc:
            # Validation errors - bad request
            logger.warning(f"Validation error on {request.method} {request.url.path}: {exc}")

            try:
                tracker = get_error_tracker()
                tracker.capture_exception(
                    exc,
                    context={
                        "method": request.method,
                        "path": request.url.path,
                        "client": request.client.host if request.client else "unknown",
                    },
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.WARNING
                )
            except RuntimeError:
                # Error tracking not initialized
                pass

            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Validation error",
                    "errors": exc.errors()
                }
            )

        except Exception as exc:
            # Unexpected errors
            logger.error(
                f"Unexpected error on {request.method} {request.url.path}: {exc}",
                exc_info=True
            )

            # Track the error
            try:
                tracker = get_error_tracker()
                tracker.capture_exception(
                    exc,
                    context={
                        "method": request.method,
                        "path": request.url.path,
                        "client": request.client.host if request.client else "unknown",
                        "query_params": dict(request.query_params),
                    },
                    category=categorize_exception(exc),
                    severity=get_error_severity(exc),
                    extra={
                        "user_agent": request.headers.get("user-agent"),
                        "referer": request.headers.get("referer"),
                    }
                )
            except RuntimeError:
                # Error tracking not initialized - log but continue
                logger.warning("Error tracking not initialized, skipping error capture")
            except Exception as tracking_error:
                # Error in error tracking - log but don't fail the request
                logger.error(f"Error tracking failed: {tracking_error}")

            # Return generic error response
            # Don't expose internal error details in production
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_type": type(exc).__name__
                }
            )


def setup_error_tracking(app) -> None:
    """
    Set up error tracking middleware and handlers.

    Args:
        app: FastAPI application instance
    """
    # Add error tracking middleware
    app.add_middleware(ErrorTrackingMiddleware)

    # Add custom exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(f"Validation error: {exc}")

        try:
            tracker = get_error_tracker()
            tracker.capture_exception(
                exc,
                context={
                    "method": request.method,
                    "path": request.url.path,
                },
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.WARNING
            )
        except RuntimeError:
            pass

        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        try:
            tracker = get_error_tracker()
            tracker.capture_exception(
                exc,
                context={
                    "method": request.method,
                    "path": request.url.path,
                },
                category=categorize_exception(exc),
                severity=ErrorSeverity.ERROR
            )
        except RuntimeError:
            pass

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    logger.info("Error tracking middleware configured")
