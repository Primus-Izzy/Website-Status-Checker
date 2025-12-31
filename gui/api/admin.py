"""
Admin API Endpoints

Provides endpoints for managing API keys and system administration.
Requires authentication with admin privileges.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from gui.auth.api_keys import (
    create_api_key,
    revoke_api_key,
    list_api_keys,
)
from gui.auth.dependencies import get_current_api_key, require_scope
from gui.database.models import APIKey
from gui.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()
logger = logging.getLogger(__name__)


# Request/Response models
class CreateAPIKeyRequest(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=3, max_length=255, description="Descriptive name for the API key")
    description: str | None = Field(None, max_length=1000, description="Optional description")
    owner_email: EmailStr | None = Field(None, description="Email of the key owner")
    owner_name: str | None = Field(None, max_length=255, description="Name of the key owner")
    expires_days: int | None = Field(None, ge=1, le=3650, description="Days until expiration (None = never)")
    rate_limit_per_hour: int = Field(1000, ge=1, le=100000, description="Maximum requests per hour")
    rate_limit_per_minute: int = Field(100, ge=1, le=10000, description="Maximum requests per minute")
    scopes: str = Field("read,write", description="Comma-separated scopes (read, write)")
    ip_whitelist: str | None = Field(None, description="Comma-separated IP addresses")


class CreateAPIKeyResponse(BaseModel):
    """Response model for creating an API key."""
    api_key: str = Field(..., description="The generated API key (save this securely!)")
    key_id: int = Field(..., description="Database ID of the API key")
    key_prefix: str = Field(..., description="First 8 characters of the key for identification")
    name: str
    created_at: datetime
    expires_at: datetime | None
    message: str = "API key created successfully. Save the key securely - it cannot be retrieved later!"


class APIKeyInfo(BaseModel):
    """Information about an API key (without the actual key)."""
    id: int
    key_prefix: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    total_requests: int
    rate_limit_per_hour: int
    rate_limit_per_minute: int
    owner_email: str | None
    owner_name: str | None
    scopes: str

    class Config:
        from_attributes = True


# Endpoints
@router.post("/api-keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    request: CreateAPIKeyRequest,
    admin_key: str | None = None,
):
    """
    Create a new API key.

    **Authentication**: Requires admin key from environment variable.

    The generated API key will only be shown once. Make sure to save it securely!

    Args:
        request: API key creation parameters
        admin_key: Admin key for authorization (from query param or header)

    Returns:
        CreateAPIKeyResponse with the generated API key

    Raises:
        HTTPException: If admin key is invalid
    """
    # Check admin key (simple approach for MVP - improve with proper admin auth later)
    if admin_key != settings.admin_api_key and admin_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )

    # Create the API key
    raw_key, api_key_model = await create_api_key(
        name=request.name,
        description=request.description,
        owner_email=request.owner_email,
        owner_name=request.owner_name,
        expires_days=request.expires_days,
        rate_limit_per_hour=request.rate_limit_per_hour,
        rate_limit_per_minute=request.rate_limit_per_minute,
        scopes=request.scopes,
        ip_whitelist=request.ip_whitelist,
    )

    logger.info(f"Created API key via admin endpoint: {api_key_model.name}")

    return CreateAPIKeyResponse(
        api_key=raw_key,
        key_id=api_key_model.id,
        key_prefix=api_key_model.key_prefix,
        name=api_key_model.name,
        created_at=api_key_model.created_at,
        expires_at=api_key_model.expires_at,
    )


@router.get("/api-keys", response_model=List[APIKeyInfo])
async def list_all_api_keys(
    admin_key: str | None = None,
):
    """
    List all API keys.

    **Authentication**: Requires admin key from environment variable.

    Returns:
        List of API key information (without the actual keys)

    Raises:
        HTTPException: If admin key is invalid
    """
    # Check admin key
    if admin_key != settings.admin_api_key and admin_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )

    api_keys = await list_api_keys()
    return [APIKeyInfo.from_orm(key) for key in api_keys]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: int,
    admin_key: str | None = None,
):
    """
    Revoke (deactivate) an API key.

    **Authentication**: Requires admin key from environment variable.

    Args:
        key_id: ID of the API key to revoke
        admin_key: Admin key for authorization

    Raises:
        HTTPException: If admin key is invalid or key not found
    """
    # Check admin key
    if admin_key != settings.admin_api_key and admin_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )

    success = await revoke_api_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {key_id} not found",
        )

    logger.info(f"Revoked API key via admin endpoint: ID {key_id}")
    return None


@router.get("/status")
async def admin_status(
    admin_key: str | None = None,
):
    """
    Get admin status and system information.

    **Authentication**: Requires admin key from environment variable.

    Returns:
        System status information

    Raises:
        HTTPException: If admin key is invalid
    """
    # Check admin key
    if admin_key != settings.admin_api_key and admin_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )

    api_keys = await list_api_keys()
    active_keys = [k for k in api_keys if k.is_active]

    return {
        "status": "healthy",
        "environment": settings.env,
        "api_keys": {
            "total": len(api_keys),
            "active": len(active_keys),
            "inactive": len(api_keys) - len(active_keys),
        },
        "authentication": {
            "enabled": True,
            "admin_key_set": bool(settings.admin_api_key or settings.secret_key),
        },
    }
