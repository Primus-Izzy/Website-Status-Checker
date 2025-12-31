"""
Database Session Management

Provides async database session management with SQLAlchemy for job persistence.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, StaticPool
from gui.config import get_settings
from gui.database.models import Base

logger = logging.getLogger(__name__)

# Global engine instance
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url

        # Convert sqlite:// to sqlite+aiosqlite:// for async support
        if database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        # Configure engine based on database type
        engine_kwargs = {
            "echo": settings.debug,
        }

        if "sqlite" in database_url:
            # SQLite-specific configuration
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # PostgreSQL/MySQL configuration
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_recycle"] = 3600

        _engine = create_async_engine(database_url, **engine_kwargs)
        logger.info(f"Database engine created: {database_url.split('@')[-1]}")  # Hide credentials

    return _engine


# Create session factory
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get the async session factory.

    Returns:
        async_sessionmaker instance
    """
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# Session factory instance
AsyncSessionLocal = get_session_factory()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.

    Usage in FastAPI:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_session)):
            ...

    Yields:
        AsyncSession instance
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in Base metadata if they don't exist.
    """
    engine = get_engine()

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")


async def close_db() -> None:
    """
    Close database connections and dispose of engine.

    Should be called on application shutdown.
    """
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


# Utility functions for common operations
async def get_db_session():
    """
    Get a database session (context manager).

    Usage:
        async with get_db_session() as session:
            result = await session.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
