"""
API Key Management Utilities

Provides functions for creating, hashing, and verifying API keys.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gui.database.models import APIKey
from gui.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.

    Returns:
        64-character hexadecimal API key

    Example:
        >>> key = generate_api_key()
        >>> len(key)
        64
    """
    return secrets.token_hex(32)  # 64 characters


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.

    Args:
        api_key: Raw API key to hash

    Returns:
        SHA-256 hash of the API key

    Example:
        >>> key = "test_key_123"
        >>> hashed = hash_api_key(key)
        >>> len(hashed)
        64
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key_hash(api_key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        api_key: Raw API key to verify
        key_hash: Stored hash to compare against

    Returns:
        True if API key matches the hash

    Example:
        >>> key = "test_key"
        >>> hashed = hash_api_key(key)
        >>> verify_api_key_hash(key, hashed)
        True
        >>> verify_api_key_hash("wrong_key", hashed)
        False
    """
    return hash_api_key(api_key) == key_hash


async def create_api_key(
    name: str,
    description: Optional[str] = None,
    owner_email: Optional[str] = None,
    owner_name: Optional[str] = None,
    expires_days: Optional[int] = None,
    rate_limit_per_hour: int = 1000,
    rate_limit_per_minute: int = 100,
    scopes: str = "read,write",
    ip_whitelist: Optional[str] = None,
) -> Tuple[str, APIKey]:
    """
    Create a new API key and store it in the database.

    Args:
        name: Descriptive name for the API key
        description: Optional description
        owner_email: Email of the key owner
        owner_name: Name of the key owner
        expires_days: Number of days until expiration (None = never)
        rate_limit_per_hour: Maximum requests per hour
        rate_limit_per_minute: Maximum requests per minute
        scopes: Comma-separated list of scopes (e.g., "read,write")
        ip_whitelist: Comma-separated list of allowed IPs

    Returns:
        Tuple of (raw_api_key, APIKey_model)
        WARNING: raw_api_key is only returned once - must be saved by caller!

    Example:
        >>> key, model = await create_api_key("test_key", owner_email="user@example.com")
        >>> print(f"Your API key: {key}")
        >>> print(f"Key ID: {model.id}")
    """
    # Generate raw API key
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:8]

    # Calculate expiration
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    # Create API key model
    api_key = APIKey(
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        description=description,
        owner_email=owner_email,
        owner_name=owner_name,
        expires_at=expires_at,
        rate_limit_per_hour=rate_limit_per_hour,
        rate_limit_per_minute=rate_limit_per_minute,
        scopes=scopes,
        ip_whitelist=ip_whitelist,
    )

    # Save to database
    async with AsyncSessionLocal() as session:
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)

    logger.info(f"Created API key: {name} (prefix: {key_prefix})")

    return raw_key, api_key


async def get_api_key_by_hash(key_hash: str) -> Optional[APIKey]:
    """
    Retrieve an API key by its hash.

    Args:
        key_hash: Hash of the API key

    Returns:
        APIKey model or None if not found
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()


async def get_api_key_by_prefix(prefix: str) -> Optional[APIKey]:
    """
    Retrieve an API key by its prefix.

    Args:
        prefix: First 8 characters of the API key

    Returns:
        APIKey model or None if not found
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(APIKey).where(APIKey.key_prefix == prefix)
        )
        return result.scalar_one_or_none()


async def verify_api_key(raw_key: str) -> Optional[APIKey]:
    """
    Verify an API key and return the model if valid.

    Args:
        raw_key: Raw API key to verify

    Returns:
        APIKey model if valid and active, None otherwise

    Checks:
        - Key exists in database
        - Key is active
        - Key has not expired
    """
    key_hash = hash_api_key(raw_key)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check expiration
        if api_key.is_expired():
            logger.warning(f"API key expired: {api_key.name}")
            return None

        # Update last used timestamp
        api_key.last_used_at = datetime.utcnow()
        api_key.total_requests += 1
        await session.commit()

        return api_key


async def revoke_api_key(key_id: int) -> bool:
    """
    Revoke (deactivate) an API key.

    Args:
        key_id: ID of the API key to revoke

    Returns:
        True if revoked successfully, False if not found
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        api_key.is_active = False
        await session.commit()

        logger.info(f"Revoked API key: {api_key.name}")
        return True


async def list_api_keys() -> list[APIKey]:
    """
    List all API keys.

    Returns:
        List of APIKey models
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(APIKey).order_by(APIKey.created_at.desc()))
        return list(result.scalars().all())
