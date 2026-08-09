"""Tests for api/routes/reviews.py"""

from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def review_routes_module() -> Any:
    return import_module("api.routes.reviews")


@pytest.fixture
def test_app(review_routes_module: Any) -> FastAPI:
    app = FastAPI()
    app.include_router(review_routes_module.router)
    return app


@pytest.fixture
def test_user() -> Mock:
    user = Mock()
    user.id = uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def empty_profile(test_user: Mock) -> Mock:
    profile = Mock()
    profile.id = uuid4()
    profile.user_id = test_user.id
    profile.github_username = None
    profile.portfolio_url = None
    profile.resume_text = None
    profile.resume_filename = None
    return profile


@pytest.fixture
def test_db() -> AsyncMock:
    db = AsyncMock()
    db.add = Mock()

    async def refresh(review: Any) -> None:
        review.id = str(uuid4())
        review.created_at = datetime.utcnow()
        review.updated_at = datetime.utcnow()

    db.refresh = AsyncMock(side_effect=refresh)
    return db


@pytest.fixture
def test_client(
    test_app: FastAPI,
    test_user: Mock,
    test_db: AsyncMock,
    review_routes_module: Any,
) -> Generator[TestClient, None, None]:
    # Endpoint relies on user and db, so I have to override them with mocks
    test_app.dependency_overrides[review_routes_module.get_current_user] = lambda: test_user

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield test_db

    test_app.dependency_overrides[review_routes_module.get_db] = override_get_db

    try:
        yield TestClient(test_app)
    finally:
        test_app.dependency_overrides.clear()


@pytest.mark.xfail(reason="POST /reviews currently accepts empty profiles instead of returning 400")
def test_post_with_empty_profile(
    test_client: TestClient,
    empty_profile: Mock,
    test_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.routes.reviews.process_review", AsyncMock())

    response = test_client.post(
        "/reviews",
        json={"profile_id": str(empty_profile.id)},
    )

    # Assert that an appropriate error is returned instead of creating a review.
    assert response.status_code == 400
    # The db should not be modified because no review should be made.
    test_db.add.assert_not_called()
    test_db.commit.assert_not_awaited()
    test_db.refresh.assert_not_awaited()
