"""Tests for health check endpoint fixes (issues #155, #154) and faithfulness checker (#153)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from api.routes.health import health_check
from rag.evaluator.faithfulness_checker import FaithfulnessChecker


@pytest.mark.unit
class TestHealthCheck:
    """Test suite for the health check endpoint behavior."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock async database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def healthy_redis(self):
        """Create a mock redis client whose ping succeeds."""
        client = MagicMock()
        client.ping = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_all_dependencies_healthy_returns_200(self, mock_db, healthy_redis):
        """Happy path: postgres, redis, and vector db all report healthy."""
        with patch("redis.from_url", return_value=healthy_redis) as mock_from_url:
            result = await health_check(db=mock_db)

        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)
        assert result["status"] == "healthy"
        assert result["dependencies"]["postgres"] == "healthy"
        assert result["dependencies"]["redis"] == "healthy"
        assert result["dependencies"]["vector_db"] == "healthy"

    @pytest.mark.asyncio
    async def test_redis_connection_uses_from_url_with_settings_url(self, mock_db, healthy_redis):
        """#155: redis.from_url is called with settings.redis_url, not settings.redis_host."""
        with patch("redis.from_url", return_value=healthy_redis) as mock_from_url:
            await health_check(db=mock_db)

        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)

    @pytest.mark.asyncio
    async def test_redis_probe_pings_connection(self, mock_db, healthy_redis):
        """#155: the health check pings the redis client to verify the connection."""
        with patch("redis.from_url", return_value=healthy_redis):
            await health_check(db=mock_db)

        healthy_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_from_url_valueerror_marks_redis_unhealthy(self, mock_db):
        """#155 failure mode: empty redis_url makes from_url raise; returns 503, not a crash."""
        with (
            patch("redis.from_url", side_effect=ValueError("Redis URL is empty")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=mock_db)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["dependencies"]["redis"] == "unhealthy"
        assert detail["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_db_probe_uses_text_wrapper(self, healthy_redis):
        """#154: db.execute is called with a text() object, not a raw SQL string."""
        db = AsyncMock()
        db.execute = AsyncMock()

        with patch("redis.from_url", return_value=healthy_redis):
            await health_check(db=db)

        call_arg = db.execute.call_args[0][0]
        assert not isinstance(call_arg, str), "DB probe must not pass a raw SQL string"
        assert isinstance(call_arg, type(text("SELECT 1"))), "DB probe must use sqlalchemy.text()"

    @pytest.mark.asyncio
    async def test_db_probe_failure_marks_postgres_unhealthy(self, healthy_redis):
        """#154 failure mode: db.execute raising marks postgres unhealthy with a 503."""
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("connection refused"))

        with (
            patch("redis.from_url", return_value=healthy_redis),
            pytest.raises(HTTPException) as exc_info,
        ):
            await health_check(db=db)

        assert exc_info.value.status_code == 503
        detail = exc_info.value.detail
        assert detail["dependencies"]["postgres"] == "unhealthy"
        assert detail["status"] == "unhealthy"


@pytest.mark.unit
class TestFaithfulnessNoneText:
    """Test suite for #153 — Faithfulness checker handles None chunk text."""

    @pytest.fixture
    def checker(self):
        """Create a FaithfulnessChecker instance."""
        return FaithfulnessChecker()

    @pytest.mark.parametrize(
        "context_chunks",
        [
            [{"text": None}],
            [{"content": "text"}],
            [{"text": None}, {"text": "Python skills"}],
            [],
        ],
    )
    def test_check_handles_none_or_missing_text(self, checker, context_chunks):
        """#153: check() returns a float score and never crashes on None/missing text."""
        score = checker.check("Has Python skills", context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_present_text_key_is_used_for_support(self, checker):
        """#153: chunks with present text still contribute to the score."""
        feedback = "The developer has strong Python skills and experience with Django."
        context_chunks = [
            {"text": "The portfolio shows Python expertise and Django framework experience."}
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert score > 0.5
