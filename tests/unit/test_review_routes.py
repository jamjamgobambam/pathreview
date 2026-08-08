"""Tests for api/routes/reviews.py.

See PLAN.md at the repo root for the reproduction notes and reasoning
behind these cases. Follows the mock-based pattern already used in
tests/unit/test_review_service.py -- no live DB/HTTP client needed, the
route function is called directly with mocked dependencies.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.routes.reviews import create_review_endpoint
from api.schemas.review import ReviewCreate


@pytest.mark.unit
class TestCreateReviewEndpointContentValidation:
    """Test suite for POST /reviews validating profile content before processing."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_background_tasks(self) -> Mock:
        bg = Mock()
        bg.add_task = Mock()
        return bg

    @pytest.fixture
    def mock_current_user(self) -> Mock:
        user = Mock()
        user.id = uuid4()
        return user

    def _mock_profile(self, **overrides: Any) -> Mock:
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        for key, value in overrides.items():
            setattr(profile, key, value)
        return profile

    @pytest.mark.asyncio
    async def test_create_review_returns_400_when_profile_has_no_ingested_content(
        self, mock_db_session: AsyncMock, mock_background_tasks: Mock, mock_current_user: Mock
    ) -> None:
        """A profile with no github_username/portfolio_url/resume_text should
        get a 400 instead of a silently-created review that will later
        fabricate placeholder feedback (see PLAN.md reproduction notes)."""
        profile_id = uuid4()
        data = ReviewCreate(profile_id=profile_id)
        empty_profile = self._mock_profile(id=profile_id)

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=empty_profile)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_review_endpoint(
                data, mock_background_tasks, mock_current_user, mock_db_session
            )

        assert exc_info.value.status_code == 400
        assert "ingestable content" in exc_info.value.detail
        mock_db_session.add.assert_not_called()
        mock_background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_returns_404_when_profile_not_found(
        self, mock_db_session: AsyncMock, mock_background_tasks: Mock, mock_current_user: Mock
    ) -> None:
        """Profile lookup returning None (wrong owner or nonexistent profile_id)
        should 404 rather than proceed."""
        data = ReviewCreate(profile_id=uuid4())

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=None)),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_review_endpoint(
                data, mock_background_tasks, mock_current_user, mock_db_session
            )

        assert exc_info.value.status_code == 404
        mock_db_session.add.assert_not_called()
        mock_background_tasks.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_review_succeeds_when_profile_has_github_username(
        self, mock_db_session: AsyncMock, mock_background_tasks: Mock, mock_current_user: Mock
    ) -> None:
        """Regression guard: the happy path must keep working once the
        content check is added -- a profile with at least one content
        field set should still create a review and schedule processing."""
        profile_id = uuid4()
        data = ReviewCreate(profile_id=profile_id)
        populated_profile = self._mock_profile(id=profile_id, github_username="octocat")

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=populated_profile)),
            patch("core.services.review_service.Review") as mock_review_cls,
        ):
            instance = mock_review_cls.return_value
            instance.id = uuid4()
            instance.profile_id = profile_id
            instance.status = "pending"
            instance.sections = None
            instance.overall_score = None
            instance.error_message = None
            instance.created_at = datetime.utcnow()
            instance.updated_at = datetime.utcnow()

            result = await create_review_endpoint(
                data, mock_background_tasks, mock_current_user, mock_db_session
            )

        assert result.status == "pending"
        mock_background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_succeeds_when_profile_has_only_resume_text(
        self, mock_db_session: AsyncMock, mock_background_tasks: Mock, mock_current_user: Mock
    ) -> None:
        """Any one of the three content fields should be sufficient -- not
        just github_username."""
        profile_id = uuid4()
        data = ReviewCreate(profile_id=profile_id)
        populated_profile = self._mock_profile(
            id=profile_id, resume_text="Experienced software engineer..."
        )

        with (
            patch("api.routes.reviews.get_profile", AsyncMock(return_value=populated_profile)),
            patch("core.services.review_service.Review") as mock_review_cls,
        ):
            instance = mock_review_cls.return_value
            instance.id = uuid4()
            instance.profile_id = profile_id
            instance.status = "pending"
            instance.sections = None
            instance.overall_score = None
            instance.error_message = None
            instance.created_at = datetime.utcnow()
            instance.updated_at = datetime.utcnow()

            result = await create_review_endpoint(
                data, mock_background_tasks, mock_current_user, mock_db_session
            )

        assert result.status == "pending"
        mock_background_tasks.add_task.assert_called_once()


@pytest.mark.unit
class TestProfileHasIngestableContent:
    """Direct tests for the new profile_has_ingestable_content helper."""

    def _mock_profile(self, **overrides: Any) -> Mock:
        profile = Mock()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        for key, value in overrides.items():
            setattr(profile, key, value)
        return profile

    def test_returns_false_when_all_fields_empty(self) -> None:
        from core.services.review_service import profile_has_ingestable_content

        assert profile_has_ingestable_content(self._mock_profile()) is False

    @pytest.mark.parametrize(
        "field",
        ["github_username", "portfolio_url", "resume_text"],
    )
    def test_returns_true_when_any_single_field_set(self, field: str) -> None:
        from core.services.review_service import profile_has_ingestable_content

        profile = self._mock_profile(**{field: "some-value"})
        assert profile_has_ingestable_content(profile) is True

    def test_returns_false_for_empty_string_fields(self) -> None:
        """Empty strings shouldn't count as content -- matches the bool()
        truthiness check in the implementation."""
        from core.services.review_service import profile_has_ingestable_content

        profile = self._mock_profile(github_username="", portfolio_url="", resume_text="")
        assert profile_has_ingestable_content(profile) is False
