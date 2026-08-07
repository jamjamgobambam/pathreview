"""Tests for the Redis-backed review cache."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from core.services.review_cache import ReviewCache


def sample_rag_output() -> dict:
    """Return a valid generated review payload."""
    return {
        "sections": [
            {
                "section_name": "Technical Skills",
                "content": "Detailed feedback",
                "confidence": 0.9,
                "suggestions": [],
            }
        ],
        "overall_score": 0.9,
    }


@pytest.mark.unit
class TestReviewCache:
    """Test content addressing, isolation, and graceful Redis fallback."""

    @pytest.fixture
    def redis_client(self) -> AsyncMock:
        """Return an asynchronous Redis mock."""
        client = AsyncMock()
        client.get = AsyncMock()
        client.setex = AsyncMock()
        return client

    @pytest.fixture
    def cache(self, redis_client: AsyncMock) -> ReviewCache:
        """Return a review cache with deterministic test configuration."""
        return ReviewCache(
            redis_client=redis_client,
            ttl_seconds=3600,
            key_version="v1",
        )

    def test_content_hash_is_stable_for_dictionary_key_order(self, cache: ReviewCache) -> None:
        """Equivalent JSON content should produce the same hash."""
        first = [{"source_type": "resume", "data": "same content"}]
        second = [{"data": "same content", "source_type": "resume"}]

        assert cache.content_hash(first) == cache.content_hash(second)

    def test_cache_key_is_isolated_by_user(self, cache: ReviewCache) -> None:
        """Different users must not share entries for identical content."""
        content = [{"source_type": "resume", "data": "same content"}]

        first_key = cache.build_key(uuid4(), content)
        second_key = cache.build_key(uuid4(), content)

        assert first_key != second_key

    def test_changed_resume_content_changes_cache_key(self, cache: ReviewCache) -> None:
        """A resume edit should invalidate the previous content key."""
        user_id = uuid4()
        original = [{"source_type": "resume", "data": "original resume"}]
        updated = [{"source_type": "resume", "data": "updated resume"}]

        assert cache.build_key(user_id, original) != cache.build_key(user_id, updated)

    def test_filename_change_does_not_change_content_key(self, cache: ReviewCache) -> None:
        """A renamed resume with unchanged content should remain a cache hit."""
        user_id = uuid4()
        original = [
            {
                "source_type": "resume",
                "filename": "resume-old.md",
                "data": "same content",
            }
        ]
        renamed = [
            {
                "source_type": "resume",
                "filename": "resume-new.md",
                "data": "same content",
            }
        ]

        assert cache.build_key(user_id, original) == cache.build_key(user_id, renamed)

    def test_source_order_does_not_change_content_key(self, cache: ReviewCache) -> None:
        """Equivalent ingestion output should not depend on source order."""
        user_id = uuid4()
        resume = {"source_type": "resume", "data": "resume"}
        github = {"source_type": "github", "data": "repositories"}

        assert cache.build_key(user_id, [resume, github]) == cache.build_key(
            user_id, [github, resume]
        )

    @pytest.mark.asyncio
    async def test_get_returns_valid_cached_output(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """Valid cached JSON should be returned as a dictionary."""
        expected = sample_rag_output()
        redis_client.get.return_value = json.dumps(expected)

        result = await cache.get(uuid4(), [{"source_type": "resume", "data": "content"}])

        assert result == expected

    @pytest.mark.asyncio
    async def test_get_treats_malformed_json_as_cache_miss(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """Malformed Redis data must not break review generation."""
        redis_client.get.return_value = "{not-json"

        result = await cache.get(uuid4(), [{"source_type": "resume", "data": "content"}])

        assert result is None

    @pytest.mark.asyncio
    async def test_get_treats_invalid_output_shape_as_cache_miss(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """Cached values without feedback sections must be ignored."""
        redis_client.get.return_value = json.dumps({"overall_score": 0.9})

        result = await cache.get(uuid4(), [{"source_type": "resume", "data": "content"}])

        assert result is None

    @pytest.mark.asyncio
    async def test_get_treats_redis_failure_as_cache_miss(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """A Redis outage should fall back to uncached processing."""
        redis_client.get.side_effect = ConnectionError("Redis unavailable")

        result = await cache.get(uuid4(), [{"source_type": "resume", "data": "content"}])

        assert result is None

    @pytest.mark.asyncio
    async def test_set_serializes_output_with_configured_ttl(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """Successful output should be stored with the configured expiry."""
        user_id = uuid4()
        content = [{"source_type": "resume", "data": "content"}]
        output = sample_rag_output()

        await cache.set(user_id, content, output)

        expected_key = cache.build_key(user_id, content)
        redis_client.setex.assert_awaited_once_with(
            expected_key,
            3600,
            json.dumps(
                output,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )

    @pytest.mark.asyncio
    async def test_set_ignores_redis_failure(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """A failed cache write must not fail the completed review."""
        redis_client.setex.side_effect = ConnectionError("Redis unavailable")

        await cache.set(
            uuid4(),
            [{"source_type": "resume", "data": "content"}],
            sample_rag_output(),
        )

        redis_client.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_skips_invalid_output(
        self, cache: ReviewCache, redis_client: AsyncMock
    ) -> None:
        """Empty or safety-rejected output must not be cached."""
        await cache.set(
            uuid4(),
            [{"source_type": "resume", "data": "content"}],
            {"sections": []},
        )

        redis_client.setex.assert_not_awaited()
