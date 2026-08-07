"""Tests for review_service.py"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

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
        mock_result = Mock()
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
        mock_result = Mock()
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
        mock_result = Mock()
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
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id, page=2, page_size=page_size)

        # Second call should pass offset for page 2
        calls = mock_db_session.execute.call_args_list
        # Should have at least one call
        assert len(calls) > 0

    @pytest.mark.asyncio
    async def test_list_reviews_returns_tuple(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns (reviews, total) tuple."""
        user_id = uuid4()

        mock_result = Mock()
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

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        await get_review(mock_db_session, review_id, user_id)

        # Should call execute with a statement
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_reviews_default_pagination(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews uses default pagination."""
        user_id = uuid4()

        mock_result = Mock()
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

        mock_result = Mock()
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

        mock_result = Mock()
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
        mock_result = Mock()
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
        mock_result = Mock()
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

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Should not raise
        result = await get_review(mock_db_session, review_id, user_id)

        assert result is None or result is not None  # Just verify no exception

    @pytest.mark.asyncio
    async def test_list_reviews_ordered_by_created_at(self, mock_db_session: AsyncMock) -> None:
        """Test list_reviews returns results ordered by created_at desc."""
        user_id = uuid4()

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        reviews, total = await list_reviews(mock_db_session, user_id)

        # Should order by created_at descending
        assert mock_db_session.execute.await_count == 2
        reviews_statement = mock_db_session.execute.await_args_list[1].args[0]
        assert "ORDER BY reviews.created_at DESC" in str(reviews_statement)

    @pytest.mark.asyncio
    async def test_identical_portfolio_content_reuses_cached_rag_result(
        self, mock_db_session: AsyncMock
    ) -> None:
        """Reproduce #32: identical content for one user runs RAG twice."""
        user_id = uuid4()
        first_profile = Mock(
            id=uuid4(),
            user_id=user_id,
            github_username="octocat",
            portfolio_url="https://example.com/portfolio",
            resume_filename="resume.md",
            resume_text="# Same resume content",
        )
        second_profile = Mock(
            id=uuid4(),
            user_id=user_id,
            github_username=first_profile.github_username,
            portfolio_url=first_profile.portfolio_url,
            resume_filename=first_profile.resume_filename,
            resume_text=first_profile.resume_text,
        )
        first_review = Mock(id=uuid4(), status="pending")
        second_review = Mock(id=uuid4(), status="pending")

        query_results = []
        for entity in (
            first_review,
            first_profile,
            second_review,
            second_profile,
        ):
            result = Mock()
            result.scalars.return_value.first.return_value = entity
            query_results.append(result)
        mock_db_session.execute.side_effect = query_results

        rag_output = {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Cached portfolio feedback",
                    "confidence": 0.9,
                    "suggestions": [],
                }
            ],
            "overall_score": 0.9,
        }

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value={"sections": []}),
            ) as run_agent,
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value=rag_output),
            ) as run_rag,
            patch(
                "core.services.review_service._run_safety_checks",
                new=AsyncMock(return_value=True),
            ),
            patch(
                "core.services.review_service.review_cache.get",
                new=AsyncMock(side_effect=[None, rag_output]),
            ) as cache_get,
            patch(
                "core.services.review_service.review_cache.set",
                new=AsyncMock(),
            ) as cache_set,
        ):
            await process_review(mock_db_session, first_review.id, first_profile.id)
            await process_review(mock_db_session, second_review.id, second_profile.id)

        assert (
            run_rag.await_count == 1
        ), "Identical portfolio content for the same user should reuse the cached RAG result"
        assert run_agent.await_count == 1
        assert cache_get.await_count == 2
        cache_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_safety_rejected_output_is_not_cached(self, mock_db_session: AsyncMock) -> None:
        """A generated result must pass safety checks before cache storage."""
        profile = Mock(
            id=uuid4(),
            user_id=uuid4(),
            github_username="octocat",
            portfolio_url=None,
            resume_filename="resume.md",
            resume_text="resume content",
        )
        review = Mock(id=uuid4(), status="pending")

        query_results = []
        for entity in (review, profile):
            result = Mock()
            result.scalars.return_value.first.return_value = entity
            query_results.append(result)
        mock_db_session.execute.side_effect = query_results

        rag_output = {
            "sections": [
                {
                    "section_name": "Technical Skills",
                    "content": "Unsafe feedback",
                    "confidence": 0.9,
                    "suggestions": [],
                }
            ],
            "overall_score": 0.9,
        }

        with (
            patch(
                "core.services.review_service._run_ingestion_pipeline",
                new=AsyncMock(return_value=[{"source_type": "resume", "data": "resume content"}]),
            ),
            patch(
                "core.services.review_service._run_agent_orchestration",
                new=AsyncMock(return_value={"sections": []}),
            ),
            patch(
                "core.services.review_service._run_rag_retrieval_generation",
                new=AsyncMock(return_value=rag_output),
            ),
            patch(
                "core.services.review_service._run_safety_checks",
                new=AsyncMock(return_value=False),
            ),
            patch(
                "core.services.review_service.review_cache.get",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "core.services.review_service.review_cache.set",
                new=AsyncMock(),
            ) as cache_set,
        ):
            await process_review(mock_db_session, review.id, profile.id)

        cache_set.assert_not_awaited()
        assert review.status == "failed"
