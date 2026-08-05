"""Database configuration and session management for async SQLAlchemy."""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

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

# Sync engine/session, for code (like the ingestion pipeline) that isn't async-native
sync_engine = create_engine(
    settings.database_url.replace("+asyncpg", "+psycopg2"),
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

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
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
