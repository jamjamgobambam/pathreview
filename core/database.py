"""Database configuration and session management for async SQLAlchemy."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from core.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create all database tables (idempotent - safe to call multiple times)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        # Log but don't fail - tables may already exist from migrations
        import structlog

        log = structlog.get_logger()
        log.debug("database_initialization", note="tables may already exist", error=str(e))


async def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
