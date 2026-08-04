"""Shared fixtures for integration tests (FastAPI TestClient + dependency overrides)."""

from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.middleware.auth import get_current_user
from core.database import get_db
from core.logging import configure_logging


@pytest.fixture(autouse=True)
def configure_test_logging():
    """Route structlog through stdlib logging so caplog can capture it."""
    configure_logging()


@pytest.fixture
def mock_db_session():
    """Create a mock async database session.

    `execute` is awaited but the sqlalchemy `Result` it returns is used
    synchronously (`.scalars().first()`), so its return value must be a
    plain `MagicMock`, not an `AsyncMock` (whose children would otherwise
    also be `AsyncMock`, turning `.scalars()` into an unawaited coroutine).
    """
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def test_user():
    """Create a mock authenticated User."""
    user = Mock()
    user.id = uuid4()
    return user


@pytest.fixture
def client(mock_db_session, test_user):
    """TestClient with auth and DB dependencies overridden."""

    async def override_get_current_user():
        return test_user

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
