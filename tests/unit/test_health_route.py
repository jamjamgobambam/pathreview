"""Tests for issue #154: Health check DB probe passes raw SQL."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session

from api.routes.health import get_db, router


def test_raw_sql_string_raises_under_sqlalchemy_2x() -> None:
    """Reproduce #154: a bare SQL string raises ArgumentError under SQLAlchemy 2.x."""
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session, pytest.raises(ArgumentError):
        session.execute("SELECT 1")


def test_wrapped_sql_string_does_not_raise() -> None:
    """Sanity check: wrapping in text() is the fix."""
    engine = create_engine("sqlite:///:memory:")
    with Session(engine) as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_health_check_returns_200_when_postgres_healthy() -> None:
    """Route-level test: /health returns 200 if DB probe passes."""
    app = FastAPI()
    app.include_router(router)

    # Mock the async DB session so we don't need a real database
    mock_db = AsyncMock()

    async def get_mock_db() -> AsyncMock:
        return mock_db

    app.dependency_overrides[get_db] = get_mock_db

    # Mock settings to prevent real environment variable lookups
    mock_settings = MagicMock()
    mock_settings.vector_db_url = "mock://url"
    mock_settings.redis_host = "localhost"
    mock_settings.redis_port = 6379

    # Mock Redis and Settings to prevent real connection attempts
    with patch("redis.Redis") as mock_redis, patch("core.config.settings", mock_settings):
        mock_redis.return_value.ping.return_value = True
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["dependencies"]["postgres"] == "healthy"
