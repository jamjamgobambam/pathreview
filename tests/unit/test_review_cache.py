"""Tests for review caching on repeated identical portfolio queries (#32).

Submitting a profile whose content is unchanged should return the stored
review instead of creating a new row and re-running the pipeline. The cache
key is a hash of the profile's content fields, and only reviews with
status="complete" are cache candidates.

Content-change invalidation is covered by the hash tests: the session double
below cannot evaluate SQL filters, so it only models whether a completed
review exists at all. The cache lookup is expected to key on
(profile_id, content_hash, status="complete").
"""

from collections.abc import Callable, Sequence
from typing import Any, cast
from uuid import uuid4

import pytest

from core.models.profile import Profile
from core.models.review import Review
from core.services.review_service import create_review


def make_profile(**overrides: str | None) -> Profile:
    """Build a Profile with representative content fields."""
    fields: dict[str, str | None] = dict(
        id=str(uuid4()),
        user_id=str(uuid4()),
        github_username="janedoe",
        portfolio_url="https://janedoe.dev",
        resume_filename="resume.pdf",
        resume_text="Jane Doe. Software Engineer. Python, FastAPI, PostgreSQL.",
    )
    fields.update(overrides)
    return Profile(**fields)


def make_review(profile: Profile, status: str = "complete") -> Review:
    """Build a Review as the pipeline would have left it."""
    return Review(
        id=str(uuid4()),
        profile_id=profile.id,
        status=status,
        sections=(
            [
                {
                    "section_name": "Technical Skills",
                    "content": "Feedback on technical skills",
                    "confidence": 0.85,
                    "suggestions": ["Add more detail on AI/ML experience"],
                }
            ]
            if status == "complete"
            else None
        ),
        overall_score=0.81 if status == "complete" else None,
    )


class _Result:
    """Stand-in for a SQLAlchemy Result."""

    def __init__(self, value: Any) -> None:
        self._value = value

    def scalars(self) -> "_Result":
        return self

    def first(self) -> Any:
        return self._value

    def all(self) -> list[Any]:
        return [self._value] if self._value is not None else []


class FakeSession:
    """Minimal async session double for the cache contract.

    Answers Profile selects with the configured profile, and Review selects
    with the first configured review whose status is "complete" — the only
    kind the contract allows as a cache hit. Records added objects so tests
    can assert whether a new row was created.
    """

    def __init__(self, profile: Profile | None = None, reviews: Sequence[Review] = ()) -> None:
        self.profile = profile
        self.reviews = list(reviews)
        self.added: list[Any] = []

    async def execute(self, stmt: Any) -> _Result:
        entity = stmt.column_descriptions[0]["entity"]
        if entity is Profile:
            return _Result(self.profile)
        if entity is Review:
            hit = next((r for r in self.reviews if r.status == "complete"), None)
            return _Result(hit)
        return _Result(None)

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        pass

    async def rollback(self) -> None:
        pass


@pytest.mark.unit
class TestContentHash:
    """Contract for the profile content hash (cache key)."""

    def _hash(self) -> Callable[[Profile], str]:
        # Imported lazily so a missing helper fails these tests without
        # breaking collection of the rest of the module. The type ignore
        # comes off once the helper exists.
        from core.services.review_service import compute_content_hash  # type: ignore[attr-defined]

        return cast(Callable[[Profile], str], compute_content_hash)

    def test_identical_content_produces_identical_hash(self) -> None:
        compute_content_hash = self._hash()
        a = make_profile()
        # Different row identity, same content: the hash must key on content.
        b = make_profile(id=str(uuid4()), user_id=str(uuid4()))

        assert compute_content_hash(a) == compute_content_hash(b)

    def test_changed_resume_text_changes_hash(self) -> None:
        compute_content_hash = self._hash()
        a = make_profile()
        b = make_profile(resume_text="Jane Doe. Senior Engineer. Python, FastAPI.")

        assert compute_content_hash(a) != compute_content_hash(b)

    def test_changed_portfolio_url_changes_hash(self) -> None:
        compute_content_hash = self._hash()
        a = make_profile()
        b = make_profile(portfolio_url="https://janedoe.io")

        assert compute_content_hash(a) != compute_content_hash(b)

    def test_all_none_content_fields_hash_stably(self) -> None:
        compute_content_hash = self._hash()
        empty = dict(
            github_username=None,
            portfolio_url=None,
            resume_filename=None,
            resume_text=None,
        )
        a = make_profile(**empty)
        b = make_profile(id=str(uuid4()), **empty)

        assert compute_content_hash(a) == compute_content_hash(b)


@pytest.mark.unit
class TestReviewCache:
    """Contract for create_review when a completed review already exists."""

    @pytest.mark.asyncio
    async def test_unchanged_resubmit_returns_stored_review(self) -> None:
        profile = make_profile()
        cached = make_review(profile, status="complete")
        db = FakeSession(profile=profile, reviews=[cached])

        result = await create_review(db, profile.id, profile.user_id)

        assert result is cached

    @pytest.mark.asyncio
    async def test_unchanged_resubmit_does_not_create_new_row(self) -> None:
        profile = make_profile()
        cached = make_review(profile, status="complete")
        db = FakeSession(profile=profile, reviews=[cached])

        await create_review(db, profile.id, profile.user_id)

        assert db.added == []

    @pytest.mark.asyncio
    async def test_no_prior_review_creates_pending_review(self) -> None:
        profile = make_profile()
        db = FakeSession(profile=profile, reviews=[])

        result = await create_review(db, profile.id, profile.user_id)

        assert result.status == "pending"
        assert len(db.added) == 1

    @pytest.mark.asyncio
    async def test_failed_review_is_not_a_cache_hit(self) -> None:
        profile = make_profile()
        failed = make_review(profile, status="failed")
        db = FakeSession(profile=profile, reviews=[failed])

        result = await create_review(db, profile.id, profile.user_id)

        assert result is not failed
        assert result.status == "pending"
        assert len(db.added) == 1
