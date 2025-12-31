"""
Rate Limiting Middleware

Implements request rate limiting to prevent abuse and protect server resources.
Uses slowapi for FastAPI integration.
"""

import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, Response
from typing import Callable

from gui.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request.

    Uses IP address as the identifier, but could be extended to use
    API keys, user IDs, etc.

    Args:
        request: FastAPI request object

    Returns:
        Identifier string for rate limiting
    """
    # Get client IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Use first IP in chain (original client)
        ip = forwarded.split(",")[0].strip()
    else:
        ip = get_remote_address(request)

    logger.debug(f"Rate limit identifier: {ip}")
    return ip


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    default_limits=[],  # No default limits, set per-route
    enabled=settings.rate_limit_enabled,
    storage_uri="memory://",  # In-memory storage (use Redis for production)
    strategy="fixed-window",  # Could also use "moving-window"
    headers_enabled=True,  # Add rate limit info to response headers
)


def setup_rate_limiting(app):
    """
    Setup rate limiting for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    if not settings.rate_limit_enabled:
        logger.warning("Rate limiting is DISABLED")
        return

    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add SlowAPI middleware
    app.add_middleware(SlowAPIMiddleware)

    # Add limiter to app state
    app.state.limiter = limiter

    logger.info(f"Rate limiting enabled: {settings.rate_limit_uploads_per_minute} uploads/min, "
                f"{settings.rate_limit_requests_per_hour} requests/hour")


# Rate limit decorators for common patterns
def upload_rate_limit():
    """Rate limit decorator for upload endpoints."""
    return limiter.limit(f"{settings.rate_limit_uploads_per_minute}/minute")


def api_rate_limit():
    """Rate limit decorator for general API endpoints."""
    return limiter.limit(f"{settings.rate_limit_requests_per_hour}/hour")


def strict_rate_limit():
    """Strict rate limit for sensitive endpoints."""
    return limiter.limit("10/minute")
