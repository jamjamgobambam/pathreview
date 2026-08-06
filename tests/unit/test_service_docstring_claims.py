"""Unit tests pinning the docstring claims in the service layer (issue #119).

The docstrings added to profile_service.py and review_service.py make claims a
reader is entitled to rely on: which arguments are actually enforced, what a
None return distinguishes, which fields a partial update leaves alone, and
whether a function can raise. A docstring that drifts from the body is worse
than no docstring, so each test here names one such claim and fails if the
behaviour stops matching the words.

Run with: make test-unit
"""

from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from api.schemas.profile import ProfileUpdate
from core.models.profile import Profile
from core.models.review import Review
from core.services.profile_service import delete_profile, get_profile, update_profile
from core.services.review_service import create_review, get_review, list_reviews, process_review

# `make test-unit` runs `pytest tests/unit -v -m unit`, so tests without the
# `unit` marker are deselected. pytest-asyncio is in strict mode (no
# asyncio_mode set in pyproject.toml), so async tests need the `asyncio` marker
# too. A list pytestmark applies both across the module.
pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _result(rows: list) -> Mock:
    """Stand in for the object AsyncSession.execute() returns.

    execute() is awaitable, but the Result it hands back is synchronous, so
    this must be a plain Mock. Building it with AsyncMock makes .scalars()
    return a coroutine instead of a ScalarResult, and every caller then fails
    with "'coroutine' object has no attribute 'first'".
    """
    result = Mock()
    result.scalars.return_value.first.return_value = rows[0] if rows else None
    result.scalars.return_value.all.return_value = rows
    return result


def _session(*row_sets: list) -> AsyncMock:
    """An AsyncSession stand-in that returns one result per execute() call.

    Each element of row_sets is the list of rows the corresponding execute()
    should yield, in call order. add() is sync on a real session; everything
    else the services touch is awaited.
    """
    db = AsyncMock()
    db.add = Mock()
    db.execute = AsyncMock(side_effect=[_result(rows) for rows in row_sets])
    return db


def _executed_statement(db: AsyncMock, call_index: int = 0) -> Any:
    """The SQLAlchemy statement passed to the call_index-th execute()."""
    return db.execute.await_args_list[call_index].args[0]


# --------------------------------------------------------------------------
# profile_service.get_profile
# --------------------------------------------------------------------------


async def test_get_profile_filters_on_both_profile_id_and_user_id() -> None:
    """Claim: returns None if the profile "does not exist or belongs to another user".

    That is only true if ownership is part of the query rather than a check the
    caller is trusted to make, so assert both columns appear in the WHERE.
    """
    db = _session([])

    await get_profile(db, str(uuid4()), str(uuid4()))

    sql = str(_executed_statement(db))
    assert "profiles.id" in sql
    assert "profiles.user_id" in sql


async def test_get_profile_returns_none_when_no_row_matches() -> None:
    """Claim: a non-matching lookup yields None rather than raising."""
    db = _session([])

    assert await get_profile(db, str(uuid4()), str(uuid4())) is None


# --------------------------------------------------------------------------
# profile_service.update_profile
# --------------------------------------------------------------------------


async def test_update_profile_leaves_none_fields_at_their_current_value() -> None:
    """Claim: "a field left as None is kept at its current value rather than cleared".

    This is the claim most likely to be got wrong by a future edit, since the
    obvious implementation assigns every field unconditionally.
    """
    profile = Profile(
        user_id=str(uuid4()),
        github_username="original-user",
        portfolio_url="https://original.example",
    )
    db = _session([profile])

    updated = await update_profile(
        db,
        str(uuid4()),
        str(uuid4()),
        ProfileUpdate(github_username="new-user", portfolio_url=None),
    )

    assert updated is not None
    assert updated.github_username == "new-user"
    assert updated.portfolio_url == "https://original.example"


async def test_update_profile_returns_none_without_committing_when_not_found() -> None:
    """Claim: returns None for a missing or someone else's profile.

    Nothing should be written on that path either.
    """
    db = _session([])

    assert await update_profile(db, str(uuid4()), str(uuid4()), ProfileUpdate()) is None
    db.commit.assert_not_awaited()


# --------------------------------------------------------------------------
# profile_service.delete_profile
# --------------------------------------------------------------------------


async def test_delete_profile_returns_false_when_profile_is_not_the_users() -> None:
    """Claim: "False if it does not exist or belongs to another user"."""
    db = _session([])

    assert await delete_profile(db, str(uuid4()), str(uuid4())) is False


async def test_delete_profile_rolls_back_and_reraises_on_failure() -> None:
    """Claim: "Exception: Re-raised after rolling back the transaction".

    Both halves matter — swallowing the error, or re-raising without the
    rollback, would each contradict the documented contract.
    """
    profile = Profile(user_id=str(uuid4()))
    db = AsyncMock()
    db.add = Mock()
    db.execute = AsyncMock(side_effect=[_result([profile]), RuntimeError("delete blew up")])

    with pytest.raises(RuntimeError, match="delete blew up"):
        await delete_profile(db, str(uuid4()), str(uuid4()))

    db.rollback.assert_awaited_once()


# --------------------------------------------------------------------------
# review_service.create_review
# --------------------------------------------------------------------------


async def test_create_review_starts_pending_with_no_sections_or_score() -> None:
    """Claim: status is "pending", while sections and overall_score stay None."""
    db = _session()

    review = await create_review(db, uuid4(), uuid4())

    assert review.status == "pending"
    assert review.sections is None
    assert review.overall_score is None


# --------------------------------------------------------------------------
# review_service.get_review
# --------------------------------------------------------------------------


async def test_get_review_enforces_ownership_inside_the_query() -> None:
    """Claim: ownership is enforced "in the query itself", via a join on profiles.

    A row that belongs to someone else is never fetched, rather than being
    fetched and then rejected in Python.
    """
    db = _session([])

    await get_review(db, uuid4(), uuid4())

    sql = str(_executed_statement(db))
    assert "JOIN profiles" in sql
    assert "profiles.user_id" in sql


# --------------------------------------------------------------------------
# review_service.list_reviews
# --------------------------------------------------------------------------


async def test_list_reviews_total_counts_all_reviews_not_just_this_page() -> None:
    """Claim: "total is the user's overall review count, not the number on this page"."""
    all_reviews = [Review(profile_id=str(uuid4())) for _ in range(5)]
    page_of_reviews = all_reviews[:2]
    db = _session(all_reviews, page_of_reviews)

    reviews, total = await list_reviews(db, uuid4(), page=1, page_size=2)

    assert len(reviews) == 2
    assert total == 5


async def test_list_reviews_orders_newest_first_and_pages_from_the_offset() -> None:
    """Claim: "newest first, with pagination" off a 1-based page number."""
    db = _session([], [])

    await list_reviews(db, uuid4(), page=3, page_size=20)

    stmt = _executed_statement(db, call_index=1)
    sql = str(stmt)
    assert "ORDER BY reviews.created_at DESC" in sql
    assert "LIMIT" in sql and "OFFSET" in sql
    # page 3 at 20 per page starts after the first 40 rows
    assert 40 in stmt.compile().params.values()


async def test_list_reviews_returns_empty_list_rather_than_raising_when_user_has_none() -> None:
    """Claim: "A user with no reviews ... gives ([], total) rather than an error"."""
    db = _session([], [])

    reviews, total = await list_reviews(db, uuid4())

    assert reviews == []
    assert total == 0


# --------------------------------------------------------------------------
# review_service.process_review
# --------------------------------------------------------------------------


async def test_process_review_never_raises_even_when_the_database_fails() -> None:
    """Claim: "Raises: Nothing."

    The outer handler catches everything, and the fallback write that records
    status="failed" is itself wrapped — so a database that fails on every call
    must still return normally.
    """
    db = AsyncMock()
    db.add = Mock()
    db.execute = AsyncMock(side_effect=RuntimeError("database is down"))

    # Declared `-> None`, so returning at all is the assertion: any exception
    # escaping here would fail the test.
    await process_review(db, uuid4(), uuid4())


async def test_process_review_changes_nothing_when_the_review_is_missing() -> None:
    """Claim: "Returns early without changing anything if no review has this ID"."""
    db = _session([])

    await process_review(db, uuid4(), uuid4())

    db.commit.assert_not_awaited()


async def test_process_review_marks_the_review_failed_when_the_profile_is_missing() -> None:
    """Claim: marks the review "failed" and returns early if the profile is missing."""
    review = Review(profile_id=str(uuid4()), status="pending")
    db = _session([review], [])

    await process_review(db, uuid4(), uuid4())

    assert review.status == "failed"
    db.commit.assert_awaited_once()


async def test_process_review_records_no_error_message_on_failure() -> None:
    """Claim: "No failure path populates reviews.error_message".

    Documented as a limitation rather than a feature: the reason a review
    failed exists only in the logs. If that is ever fixed, this test should
    fail and the docstring should change with it.
    """
    review = Review(profile_id=str(uuid4()), status="pending")
    db = _session([review], [])

    await process_review(db, uuid4(), uuid4())

    assert review.status == "failed"
    assert review.error_message is None
