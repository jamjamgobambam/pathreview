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


def make_db(
    first_return: object = None,
    all_return: object = None,
) -> AsyncMock:
    """
    Factory that builds a correctly-shaped async db mock.
    Only execute() is async — scalars/first/all are plain Mock.
    """
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = first_return
    mock_result.scalars.return_value.all.return_value = all_return if all_return is not None else []
    db.execute = AsyncMock(return_value=mock_result)
    return db


@pytest.mark.unit
class TestCreateReview:
    """Tests for create_review()"""

    @pytest.mark.asyncio
    async def test_returns_review_with_pending_status(self) -> None:
        db = make_db()
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_instance = Mock()
            mock_instance.status = "pending"
            mock_review_class.return_value = mock_instance

            await create_review(db, profile_id, user_id)

            call_kwargs = mock_review_class.call_args[1]
            assert call_kwargs["status"] == "pending"

    @pytest.mark.asyncio
    async def test_sections_and_score_initially_none(self) -> None:
        db = make_db()
        profile_id = uuid4()
        user_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_review_class.return_value = Mock()
            await create_review(db, profile_id, user_id)

            call_kwargs = mock_review_class.call_args[1]
            assert call_kwargs["sections"] is None
            assert call_kwargs["overall_score"] is None

    @pytest.mark.asyncio
    async def test_calls_db_add(self) -> None:
        db = make_db()
        with patch("core.services.review_service.Review"):
            await create_review(db, uuid4(), uuid4())
            db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_db_commit(self) -> None:
        db = make_db()
        with patch("core.services.review_service.Review"):
            await create_review(db, uuid4(), uuid4())
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_db_refresh(self) -> None:
        db = make_db()
        with patch("core.services.review_service.Review"):
            await create_review(db, uuid4(), uuid4())
            db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_profile_id_passed_to_review(self) -> None:
        db = make_db()
        profile_id = uuid4()

        with patch("core.services.review_service.Review") as mock_review_class:
            mock_review_class.return_value = Mock()
            await create_review(db, profile_id, uuid4())

            call_kwargs = mock_review_class.call_args[1]
            assert call_kwargs["profile_id"] == profile_id


@pytest.mark.unit
class TestGetReview:
    """Tests for get_review()"""

    @pytest.mark.asyncio
    async def test_returns_review_for_correct_owner(self) -> None:
        mock_review = Mock()
        db = make_db(first_return=mock_review)

        result = await get_review(db, uuid4(), uuid4())
        assert result == mock_review

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = make_db(first_return=None)

        result = await get_review(db, uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_calls_db_execute(self) -> None:
        db = make_db(first_return=None)

        await get_review(db, uuid4(), uuid4())
        db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_user(self) -> None:
        db = make_db(first_return=None)

        result = await get_review(db, uuid4(), uuid4())
        assert result is None


@pytest.mark.unit
class TestListReviews:
    """Tests for list_reviews()"""

    @pytest.mark.asyncio
    async def test_returns_tuple(self) -> None:
        db = make_db(all_return=[])
        result = await list_reviews(db, uuid4())
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_list_and_int(self) -> None:
        db = make_db(all_return=[])
        reviews, total = await list_reviews(db, uuid4())
        assert isinstance(reviews, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_total_reflects_all_results(self) -> None:
        mock_reviews = [Mock() for _ in range(5)]
        db = make_db(all_return=mock_reviews)

        reviews, total = await list_reviews(db, uuid4())
        assert total == 5

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        db = make_db(all_return=[])
        reviews, total = await list_reviews(db, uuid4())
        assert reviews == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_default_pagination_calls_execute(self) -> None:
        db = make_db(all_return=[])
        await list_reviews(db, uuid4())
        assert db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_custom_page_size(self) -> None:
        db = make_db(all_return=[])
        reviews, total = await list_reviews(db, uuid4(), page=1, page_size=50)
        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_page_2_calls_execute(self) -> None:
        db = make_db(all_return=[])
        await list_reviews(db, uuid4(), page=2, page_size=20)
        assert db.execute.call_count == 2


@pytest.mark.unit
class TestProcessReview:
    """Tests for process_review() - the main pipeline function."""

    @pytest.mark.asyncio
    async def test_sets_status_failed_when_review_not_found(self) -> None:
        db = make_db(first_return=None)

        await process_review(db, uuid4(), uuid4())
        db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_sets_status_failed_when_profile_not_found(self) -> None:
        mock_review = Mock()
        mock_review.status = "pending"

        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()

        mock_result_with_review = Mock()
        mock_result_with_review.scalars.return_value.first.return_value = mock_review

        mock_result_no_profile = Mock()
        mock_result_no_profile.scalars.return_value.first.return_value = None

        db.execute = AsyncMock(side_effect=[mock_result_with_review, mock_result_no_profile])

        await process_review(db, uuid4(), uuid4())
        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_sets_status_complete_on_success(self) -> None:
        mock_review = Mock()
        mock_review.status = "pending"
        mock_profile = Mock()
        mock_profile.github_username = None
        mock_profile.portfolio_url = None
        mock_profile.resume_text = None

        mock_result_review = Mock()
        mock_result_review.scalars.return_value.first.return_value = mock_review

        mock_result_profile = Mock()
        mock_result_profile.scalars.return_value.first.return_value = mock_profile

        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.execute = AsyncMock(side_effect=[mock_result_review, mock_result_profile])

        with (
            patch("core.services.review_service._run_agent_orchestration") as mock_agent,
            patch("core.services.review_service._run_rag_retrieval_generation") as mock_rag,
            patch("core.services.review_service._run_safety_checks") as mock_safety,
        ):
            mock_agent.return_value = {"sections": [], "overall_score": 0.8}
            mock_rag.return_value = {
                "sections": [
                    {
                        "section_name": "Skills",
                        "content": "Good",
                        "confidence": 0.8,
                        "suggestions": [],
                    }
                ],
                "overall_score": 0.8,
            }
            mock_safety.return_value = True

            await process_review(db, uuid4(), uuid4())

        assert mock_review.status == "complete"

    @pytest.mark.asyncio
    async def test_sets_status_failed_when_safety_checks_fail(self) -> None:
        mock_review = Mock()
        mock_review.status = "pending"
        mock_profile = Mock()
        mock_profile.github_username = None
        mock_profile.portfolio_url = None
        mock_profile.resume_text = None

        mock_result_review = Mock()
        mock_result_review.scalars.return_value.first.return_value = mock_review

        mock_result_profile = Mock()
        mock_result_profile.scalars.return_value.first.return_value = mock_profile

        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.execute = AsyncMock(side_effect=[mock_result_review, mock_result_profile])

        with (
            patch("core.services.review_service._run_agent_orchestration") as mock_agent,
            patch("core.services.review_service._run_rag_retrieval_generation") as mock_rag,
            patch("core.services.review_service._run_safety_checks") as mock_safety,
        ):
            mock_agent.return_value = {"sections": [], "overall_score": 0.0}
            mock_rag.return_value = {"sections": [], "overall_score": 0.0}
            mock_safety.return_value = False

            await process_review(db, uuid4(), uuid4())

        assert mock_review.status == "failed"

    @pytest.mark.asyncio
    async def test_exception_sets_status_failed(self) -> None:
        mock_review = Mock()
        mock_review.status = "pending"

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_review

        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)

        with patch(
            "core.services.review_service._run_ingestion_pipeline",
            side_effect=Exception("pipeline exploded"),
        ):
            await process_review(db, uuid4(), uuid4())

        assert mock_review.status == "failed"
