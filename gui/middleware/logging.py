"""
Request/Response Logging Middleware for FastAPI

Provides comprehensive request and response logging with:
- Request/response timing
- Correlation IDs for request tracking
- Structured logging with context
- Performance metrics
- Configurable log levels by endpoint
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers

from src.utils.logging_config import get_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses with timing and context.

    Features:
    - Assigns correlation ID to each request
    - Logs request method, path, client info
    - Logs response status code and timing
    - Supports structured JSON logging
    - Excludes health check endpoints from logging
    """

    def __init__(
        self,
        app,
        exclude_paths: list[str] = None,
        log_request_body: bool = False,
        log_response_body: bool = False
    ):
        """
        Initialize request logging middleware.

        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from logging (e.g., ["/health", "/metrics"])
            log_request_body: Whether to log request bodies (security risk for sensitive data)
            log_response_body: Whether to log response bodies (can be verbose)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/health/live", "/health/ready", "/metrics"]
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.logger = logging.getLogger("api.requests")

    def should_log_path(self, path: str) -> bool:
        """
        Check if path should be logged.

        Args:
            path: Request path

        Returns:
            True if should log, False otherwise
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        return True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Check if we should log this path
        if not self.should_log_path(request.url.path):
            return await call_next(request)

        # Get logger with correlation ID
        logger = get_logger(__name__, correlation_id=correlation_id)

        # Record start time
        start_time = time.time()

        # Extract request info
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request
        logger.info(
            f"{method} {path}",
            extra={
                "event_type": "http_request",
                "method": method,
                "path": path,
                "client_ip": client_host,
                "user_agent": user_agent,
                "query_params": query_params if query_params else None,
            }
        )

        # Log request body if enabled (be careful with sensitive data)
        if self.log_request_body and method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                logger.debug(
                    f"Request body: {body[:500]}",  # Limit to first 500 bytes
                    extra={
                        "event_type": "http_request_body",
                        "body_preview": body[:500].decode('utf-8', errors='ignore')
                    }
                )
            except Exception as e:
                logger.warning(f"Could not read request body: {e}")

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log error and re-raise
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"{method} {path} - Exception after {duration_ms:.2f}ms",
                extra={
                    "event_type": "http_error",
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True
            )
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Determine log level based on status code
        status_code = response.status_code
        if status_code < 400:
            log_method = logger.info
        elif status_code < 500:
            log_method = logger.warning
        else:
            log_method = logger.error

        # Log response
        log_method(
            f"{method} {path} - {status_code} in {duration_ms:.2f}ms",
            extra={
                "event_type": "http_response",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_host,
            }
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests and track performance metrics.

    Logs warnings for requests that exceed configured thresholds.
    """

    def __init__(
        self,
        app,
        slow_request_threshold_ms: float = 1000,
        very_slow_request_threshold_ms: float = 5000
    ):
        """
        Initialize performance logging middleware.

        Args:
            app: FastAPI application
            slow_request_threshold_ms: Threshold for slow request warning
            very_slow_request_threshold_ms: Threshold for very slow request error
        """
        super().__init__(app)
        self.slow_threshold = slow_request_threshold_ms
        self.very_slow_threshold = very_slow_request_threshold_ms
        self.logger = logging.getLogger("api.performance")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with performance tracking.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Get correlation ID if available
        correlation_id = getattr(request.state, "correlation_id", None)

        # Log slow requests
        if duration_ms > self.very_slow_threshold:
            logger = get_logger(__name__, correlation_id=correlation_id)
            logger.error(
                f"Very slow request: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                extra={
                    "event_type": "very_slow_request",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "threshold_ms": self.very_slow_threshold,
                }
            )
        elif duration_ms > self.slow_threshold:
            logger = get_logger(__name__, correlation_id=correlation_id)
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration_ms:.2f}ms",
                extra={
                    "event_type": "slow_request",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "threshold_ms": self.slow_threshold,
                }
            )

        return response


def setup_request_logging(
    app,
    exclude_paths: list[str] = None,
    log_request_body: bool = False,
    log_response_body: bool = False,
    enable_performance_logging: bool = True,
    slow_request_threshold_ms: float = 1000
) -> None:
    """
    Set up request logging middleware.

    Args:
        app: FastAPI application
        exclude_paths: Paths to exclude from logging
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        enable_performance_logging: Whether to enable performance logging
        slow_request_threshold_ms: Threshold for slow request warnings
    """
    # Add request logging middleware
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=exclude_paths,
        log_request_body=log_request_body,
        log_response_body=log_response_body
    )

    # Add performance logging middleware
    if enable_performance_logging:
        app.add_middleware(
            PerformanceLoggingMiddleware,
            slow_request_threshold_ms=slow_request_threshold_ms,
            very_slow_request_threshold_ms=slow_request_threshold_ms * 5
        )

    logging.getLogger(__name__).info("Request logging middleware configured")
