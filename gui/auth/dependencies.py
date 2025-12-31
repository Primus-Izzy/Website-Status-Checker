"""
FastAPI Authentication Dependencies

Provides dependency injection for API key authentication.
"""

import logging
from typing import Optional
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from datetime import datetime, timedelta

from gui.database.models import APIKey
from gui.auth.api_keys import verify_api_key, hash_api_key

logger = logging.getLogger(__name__)

# Define API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting tracking (in-memory for now)
rate_limit_tracker: dict[str, list[datetime]] = {}


async def get_current_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> APIKey:
    """
    Dependency to get and verify the current API key.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Verified APIKey model

    Raises:
        HTTPException: If API key is missing, invalid, or rate limited

    Usage:
        @app.get("/protected")
        async def protected_endpoint(api_key: APIKey = Depends(get_current_api_key)):
            return {"message": f"Hello {api_key.name}"}
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Verify API key
    verified_key = await verify_api_key(api_key)

    if not verified_key:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Check rate limits
    key_hash = hash_api_key(api_key)
    now = datetime.utcnow()

    # Initialize tracker for this key if needed
    if key_hash not in rate_limit_tracker:
        rate_limit_tracker[key_hash] = []

    # Clean old requests (older than 1 hour)
    rate_limit_tracker[key_hash] = [
        req_time for req_time in rate_limit_tracker[key_hash]
        if now - req_time < timedelta(hours=1)
    ]

    # Check hourly rate limit
    requests_last_hour = len(rate_limit_tracker[key_hash])
    if requests_last_hour >= verified_key.rate_limit_per_hour:
        logger.warning(f"Rate limit exceeded for API key: {verified_key.name}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {verified_key.rate_limit_per_hour} requests per hour",
            headers={"Retry-After": "3600"},
        )

    # Check minute rate limit
    one_minute_ago = now - timedelta(minutes=1)
    requests_last_minute = sum(
        1 for req_time in rate_limit_tracker[key_hash]
        if req_time > one_minute_ago
    )
    if requests_last_minute >= verified_key.rate_limit_per_minute:
        logger.warning(f"Minute rate limit exceeded for API key: {verified_key.name}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {verified_key.rate_limit_per_minute} requests per minute",
            headers={"Retry-After": "60"},
        )

    # Record this request
    rate_limit_tracker[key_hash].append(now)

    logger.debug(f"API key verified: {verified_key.name}")
    return verified_key


def require_scope(required_scope: str):
    """
    Dependency factory to require a specific scope.

    Args:
        required_scope: The scope required for this endpoint (e.g., "write")

    Returns:
        Dependency function

    Usage:
        @app.post("/data")
        async def create_data(api_key: APIKey = Depends(require_scope("write"))):
            ...
    """
    async def scope_checker(api_key: APIKey = Security(get_current_api_key)) -> APIKey:
        if not api_key.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}",
            )
        return api_key

    return scope_checker


async def get_optional_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[APIKey]:
    """
    Dependency to optionally get an API key (doesn't require it).

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Verified APIKey model or None if no key provided

    Usage:
        @app.get("/public-or-private")
        async def endpoint(api_key: Optional[APIKey] = Depends(get_optional_api_key)):
            if api_key:
                return {"message": f"Hello {api_key.name}"}
            return {"message": "Hello anonymous"}
    """
    if not api_key:
        return None

    try:
        return await get_current_api_key(api_key)
    except HTTPException:
        return None


async def check_ip_whitelist(request: Request, api_key: APIKey = Security(get_current_api_key)) -> APIKey:
    """
    Dependency to check IP whitelist for an API key.

    Args:
        request: FastAPI request object
        api_key: Verified API key

    Returns:
        APIKey if IP is whitelisted

    Raises:
        HTTPException: If IP is not in whitelist

    Usage:
        @app.get("/restricted")
        async def restricted_endpoint(api_key: APIKey = Depends(check_ip_whitelist)):
            ...
    """
    if not api_key.ip_whitelist:
        return api_key  # No whitelist = allow all IPs

    client_ip = request.client.host if request.client else None
    if not client_ip:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to determine client IP",
        )

    allowed_ips = [ip.strip() for ip in api_key.ip_whitelist.split(',')]
    if client_ip not in allowed_ips:
        logger.warning(f"IP {client_ip} not in whitelist for API key: {api_key.name}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"IP address {client_ip} is not authorized",
        )

    return api_key
