"""Reproduction test for issue #88.

A profile with no ingested documents (no GitHub username, no portfolio URL,
no resume text) produces zero ingested sources, yet process_review still
marks the review "complete" with fabricated sections and a score.

This test documents the CURRENT (incorrect) behavior so the bug is proven
before the fix. Its assertions must be updated once the fix lands.
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from core.services.review_service import process_review


@pytest.mark.unit
class TestIssue88Repro:
    """Reproduces the empty-profile review path for issue #88."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Mock async DB session; no real database is required."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_review(self) -> Mock:
        """A freshly created review, as POST /reviews would produce it."""
        review = Mock()
        review.id = uuid4()
        review.status = "pending"
        review.sections = None
        review.overall_score = None
        return review

    @pytest.fixture
    def mock_empty_profile(self) -> Mock:
        """A profile with no ingested documents: the condition in issue #88."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None
        profile.resume_filename = None
        return profile

    @pytest.mark.asyncio
    async def test_empty_profile_still_yields_complete_review(
        self,
        mock_db_session: AsyncMock,
        mock_review: Mock,
        mock_empty_profile: Mock,
    ) -> None:
        """process_review fabricates a complete review from zero sources."""
        review_result = Mock()
        review_result.scalars.return_value.first.return_value = mock_review

        profile_result = Mock()
        profile_result.scalars.return_value.first.return_value = mock_empty_profile

        # process_review calls db.execute twice: once for the review, once
        # for the profile. side_effect returns them in that order.
        mock_db_session.execute = AsyncMock(side_effect=[review_result, profile_result])

        await process_review(mock_db_session, mock_review.id, mock_empty_profile.id)

        print("\n--- OBSERVED ---")
        print("status       :", mock_review.status)
        print("overall_score:", mock_review.overall_score)
        print("num sections :", len(mock_review.sections))

        # Current behavior (the bug): zero real input, confident output.
        assert mock_review.status == "complete"
        assert mock_review.overall_score == 0.81
        assert len(mock_review.sections) == 3
