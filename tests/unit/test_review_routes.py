"""Tests for api/routes/reviews.py"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.auth import get_current_user
from api.routes import reviews
from core.database import get_db


@pytest.mark.unit
def test_create_review_profile_with_no_ingested_content_returns_400(monkeypatch):
    """POST /reviews should return 400 when the profile has nothing to ingest."""
    user = Mock()
    user.id = uuid4()
    empty_profile = Mock(
        id=uuid4(),
        user_id=user.id,
        github_username=None,
        resume_text=None,
        portfolio_url=None,
    )

    async def fake_get_profile(db, profile_id, user_id):
        return empty_profile

    monkeypatch.setattr(reviews, "get_profile", fake_get_profile)

    app = FastAPI()
    app.include_router(reviews.router)
    app.dependency_overrides[get_current_user] = lambda: user

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_db

    response = TestClient(app).post(
        "/reviews",
        json={"profile_id": str(empty_profile.id)},
    )

    assert response.status_code == 400
    assert "no ingested content" in response.json()["detail"].lower()
