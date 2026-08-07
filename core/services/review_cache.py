"""Redis-backed cache for generated portfolio reviews."""

import hashlib
import json
from typing import Any, cast
from uuid import UUID

import structlog
from redis import asyncio as redis

from core.config import settings

log = structlog.get_logger()


class ReviewCache:
    """Store complete RAG outputs using user-scoped content hashes."""

    _NON_CONTENT_FIELDS = frozenset(
        {
            "profile_id",
            "review_id",
            "resume_filename",
            "filename",
        }
    )

    def __init__(
        self,
        redis_client: Any,
        ttl_seconds: int,
        key_version: str,
    ) -> None:
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        self.key_version = key_version

    @staticmethod
    def content_hash(ingestion_results: list[dict]) -> str:
        """Return a stable SHA-256 hash for canonically serialized content."""
        normalized_sources = [
            {
                key: value
                for key, value in source.items()
                if key not in ReviewCache._NON_CONTENT_FIELDS
            }
            for source in ingestion_results
        ]
        normalized_sources.sort(
            key=lambda source: json.dumps(
                source,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        canonical_content = json.dumps(
            normalized_sources,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()

    def build_key(
        self,
        user_id: UUID | str,
        ingestion_results: list[dict],
    ) -> str:
        """Build an opaque cache key isolated to one user."""
        digest = self.content_hash(ingestion_results)
        return f"pathreview:review:{self.key_version}:{user_id}:{digest}"

    async def get(
        self,
        user_id: UUID | str,
        ingestion_results: list[dict],
    ) -> dict | None:
        """Return a cached RAG output or None when it cannot be safely used."""
        key = self.build_key(user_id, ingestion_results)

        try:
            cached_value = await self.redis.get(key)
            if cached_value is None:
                log.info("review_cache_miss", cache_key=key)
                return None

            parsed: object = json.loads(cached_value)
            if not self._is_valid_output(parsed):
                log.warning("review_cache_invalid_value", cache_key=key)
                return None

            log.info("review_cache_hit", cache_key=key)
            return cast("dict", parsed)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as exc:
            log.warning(
                "review_cache_deserialization_failed",
                cache_key=key,
                error=str(exc),
            )
            return None
        except Exception as exc:
            log.warning(
                "review_cache_read_failed",
                cache_key=key,
                error=str(exc),
            )
            return None

    async def set(
        self,
        user_id: UUID | str,
        ingestion_results: list[dict],
        rag_output: dict,
    ) -> None:
        """Cache a valid RAG output, ignoring Redis and serialization errors."""
        key = self.build_key(user_id, ingestion_results)

        if not self._is_valid_output(rag_output):
            log.warning("review_cache_write_skipped_invalid_value", cache_key=key)
            return

        try:
            serialized = json.dumps(
                rag_output,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            await self.redis.setex(key, self.ttl_seconds, serialized)
            log.info(
                "review_cache_stored",
                cache_key=key,
                ttl_seconds=self.ttl_seconds,
            )
        except (TypeError, ValueError) as exc:
            log.warning(
                "review_cache_serialization_failed",
                cache_key=key,
                error=str(exc),
            )
        except Exception as exc:
            log.warning(
                "review_cache_write_failed",
                cache_key=key,
                error=str(exc),
            )

    @staticmethod
    def _is_valid_output(value: object) -> bool:
        """Check the minimum shape required before safety validation."""
        if not isinstance(value, dict):
            return False
        sections = value.get("sections")
        return isinstance(sections, list) and bool(sections)


redis_client = redis.from_url(settings.redis_url, decode_responses=True)
review_cache = ReviewCache(
    redis_client=redis_client,
    ttl_seconds=settings.review_cache_ttl_seconds,
    key_version=settings.review_cache_key_version,
)
