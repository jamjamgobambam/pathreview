"""Tests for the /health endpoint safety-events wiring (api/routes/health.py)."""

# mypy: ignore-errors
# (tests aren't type-checked; see `make typecheck`, which excludes tests/)

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from api.routes import health


class FakeRedis:
    """Minimal in-memory Redis stand-in for the health check."""

    def __init__(self, store=None):
        self.store = store or {}

    def ping(self):
        return True

    def get(self, key):
        value = self.store.get(key)
        return None if value is None else str(value)


@pytest.mark.unit
class TestHealthSafetyEvents:
    """The endpoint reports the real safety-event count, not a constant 0."""

    @pytest.fixture
    def mock_db(self):
        """A DB session whose execute() succeeds (postgres reported healthy)."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    @pytest.mark.asyncio
    async def test_reports_real_safety_event_count(self, mock_db):
        """With events recorded, safety_events_last_hour reflects the total."""
        fake = FakeRedis(
            {
                "safety:events:pii_detected": 2,
                "safety:events:injection_attempt": 1,
            }
        )
        with patch("redis.Redis.from_url", return_value=fake):
            result = await health.health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 3
        assert result["dependencies"]["redis"] == "healthy"

    @pytest.mark.asyncio
    async def test_zero_when_no_events_recorded(self, mock_db):
        """No recorded events legitimately reports 0."""
        with patch("redis.Redis.from_url", return_value=FakeRedis({})):
            result = await health.health_check(db=mock_db)

        assert result["safety_events_last_hour"] == 0

    @pytest.mark.asyncio
    async def test_falls_back_to_zero_when_redis_down(self, mock_db):
        """Redis being down degrades gracefully: count 0, redis unhealthy, 503."""
        with (
            patch("redis.Redis.from_url", side_effect=Exception("redis down")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health.health_check(db=mock_db)

        detail = exc_info.value.detail
        assert exc_info.value.status_code == 503
        assert detail["safety_events_last_hour"] == 0
        assert detail["dependencies"]["redis"] == "unhealthy"
