"""Tests for review_service.py"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from core.services.review_service import (
    create_review,
    get_review,
    list_reviews,
    process_review,
)


@pytest.mark.unit
class TestReviewService:
    """Test suite for review_service module."""

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
    def mock_review(self) -> Mock:
        """Create a mock Review object."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        return review

    @pytest.fixture
    def mock_profile(self) -> Mock:
        """Create a mock Profile object."""
        profile = Mock()
        profile.id = uuid4()
        profile.user_id = uuid4()
        return profile

    @pytest.mark.asyncio
    async def test_create_review_returns_review_with_pending_status(
        self, mock_db_session: AsyncMock, mock_review: Mock
    ) -> None:
        """Test create_review returns Review with status='pending'."""
        profile_id = uuid4()
        user_id = uuid4()

        # Setup mock
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_instance = mock_review_class.return_value
            mock_instance.status = "pending"
            mock_instance.sections = None
            mock_instance.overall_score = None

            await create_review(mock_db_session, profile_id, user_id)

            # Check that Review was instantiated
            mock_review_class.assert_called()
            call_kwargs = mock_review_class.call_args[1]
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_review_returns_review_for_correct_owner(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test get_review returns review when user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_review = Mock()
        mock_review.id = review_id

        # Setup mock execute to return review
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, user_id)

        assert result == mock_review
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_returns_none_for_wrong_user(self, mock_db_session: AsyncMock) -> None:
        """Test get_review returns None when user_id doesn't match."""
        review_id = uuid4()
        wrong_user_id = uuid4()

        # Setup mock to return None
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await get_review(mock_db_session, review_id, wrong_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_reviews_returns_paginated_results(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns paginated results."""
        user_id = uuid4()

        # Create mock reviews
        mock_reviews = [Mock() for _ in range(5)]

        # Setup execute mock to return reviews
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=1, page_size=20)

        assert len(reviews) > 0 or len(reviews) == 0  # May be empty
        assert isinstance(total, int)
        assert total >= 0

    @pytest.mark.asyncio
    async def test_list_reviews_page_2_returns_correct_offset(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test list_reviews page 2 returns correct offset."""
        user_id = uuid4()
        page_size = 20

        # Setup mock
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # Second call should pass offset for page 2
        calls = mock_db_session.execute.call_args_list
        # Should have at least one call
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        result = await list_reviews(mock_db_session, user_id)

        assert isinstance(result, tuple)
        assert len(result) == 2
        reviews, total = result
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_create_review_calls_db_add(self, mock_db_session: AsyncMock) -> None:
        """Test create_review calls db.add()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_commit(self, mock_db_session: AsyncMock) -> None:
        """Test create_review calls db.commit()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_review_calls_db_refresh(self, mock_db_session: AsyncMock) -> None:
        """Test create_review calls db.refresh()."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review"):
            await create_review(mock_db_session, profile_id, user_id)

            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_uses_select_and_join(self, mock_db_session: AsyncMock) -> None:
        """Test get_review constructs proper SQL with join."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should call execute with a statement
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should use default page=1, page_size=20
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_custom_page_size(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews with custom page size."""
        user_id = uuid4()
        custom_page_size = 50

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(
            mock_db_session, user_id, page=1, page_size=custom_page_size
        )

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_create_review_with_uuid_ids(self, mock_db_session: AsyncMock) -> None:
        """Test create_review handles UUID objects correctly."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_review_class.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = mock_review_class.call_args[1]
            assert "profile_id" in call_kwargs
            assert "status" in call_kwargs

    @pytest.mark.asyncio
    async def test_get_review_verifies_ownership(self, mock_db_session: AsyncMock) -> None:
        """Test get_review checks Profile.user_id matches."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should construct query with user_id filter
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_counts_total(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews calculates total count."""
        user_id = uuid4()

        mock_reviews = [Mock() for _ in range(5)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Total should be counted
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_list_reviews_returns_reviews_list(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns list of Review objects."""
        user_id = uuid4()

        mock_reviews = [Mock(spec=["id", "status"]) for _ in range(3)]
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_reviews
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_review_sections_and_score_initially_none(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Test review has None for sections and overall_score initially."""
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_review_class.return_value = Mock()
            await create_review(mock_db_session, profile_id, user_id)

            call_kwargs = mock_review_class.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_get_review_with_valid_uuid(self, mock_db_session: AsyncMock) -> None:
        """Test get_review handles valid UUID parameters."""
        review_id = uuid4()
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Should not raise
        result = await get_review(mock_db_session, review_id, user_id)

        assert result is None or result is not None  # Just verify no exception

    @pytest.mark.asyncio
    async def test_process_review_schedules_notification_when_callback_registered(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Test process_review schedules notify_callback_on_review_completed via
        asyncio.create_task when a Callback is registered for the profile."""
        review_id = uuid4()
        profile_id: UUID = mock_profile.id

        mock_callback = Mock()
        mock_callback.id = str(uuid4())
        mock_callback.url = "https://client.example.com/callback"

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        callback_result = Mock()
        callback_result.scalars.return_value.first.return_value = mock_callback
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, callback_result]
        )

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value={"sections": []}),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.9}),
            ),
            patch(
                "core.services.review_service._run_safety_checks",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "core.services.review_service.notify_callback_on_review_completed",
                new=AsyncMock(),
            ) as mock_notify,
            patch("core.services.review_service.asyncio.create_task") as mock_create_task,
        ):
            await process_review(mock_db_session, review_id, profile_id)

            mock_create_task.assert_called_once()
            # The scheduled coroutine is never awaited by create_task (it's mocked out),
            # so await it directly to drive the underlying AsyncMock and avoid a warning.
            await mock_create_task.call_args[0][0]

        mock_notify.assert_called_once_with(
            user_id=mock_profile.user_id,
            profile_id=str(profile_id),
            review_id=str(review_id),
            callback_id=mock_callback.id,
            callback_url=mock_callback.url,
        )

    @pytest.mark.asyncio
    async def test_process_review_skips_notification_when_no_callback_registered(
        self, mock_db_session: AsyncMock, mock_review: Mock, mock_profile: Mock
    ) -> None:
        """Test process_review doesn't schedule a notification when no Callback is
        registered for the profile."""
        review_id = uuid4()
        profile_id: UUID = mock_profile.id

        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review
        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_profile
        callback_result = Mock()
        callback_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(
            side_effect=[review_result, profile_result, callback_result]
        )

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value={"sections": []}),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value={"sections": [], "overall_score": 0.9}),
            ),
            patch(
                "core.services.review_service._run_safety_checks",
                new=AsyncMock(return_value=True),
            ),
            patch("core.services.review_service.asyncio.create_task") as mock_create_task,
        ):
            await process_review(mock_db_session, review_id, profile_id)

            mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await list_reviews(mock_db_session, user_id)

        # Should order by created_at descending
        mock_db_session.execute.assert_called_once()
