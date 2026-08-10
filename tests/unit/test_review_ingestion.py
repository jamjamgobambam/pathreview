"""Tests for the ingestion-pipeline helper in review_service.py."""

import json
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from core.services.review_service import _run_ingestion_pipeline


@pytest.mark.unit
class TestRunIngestionPipeline:
    """Coverage for _run_ingestion_pipeline persistence behavior."""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def profile_all_sources(self) -> Mock:
        """A Profile with all three ingestible sources present."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = "octocat"
        profile.portfolio_url = "https://example.com/portfolio"
        profile.resume_text = "Experienced software engineer."
        profile.resume_filename = "resume.pdf"
        return profile

    @pytest.mark.asyncio
    async def test_persists_all_sources_without_error(
        self, mock_db_session: AsyncMock, profile_all_sources: Mock
    ) -> None:
        """Regression test: IngestedSource() used to be constructed with a
        raw_data kwarg that didn't exist as a column, raising TypeError on
        every call -- but each call site swallowed it via a bare
        `except Exception`, so nothing was ever persisted despite no visible
        error to the caller. Confirms db.add() is now actually reached and no
        error is logged for any of the three sources.
        """
        with patch("core.services.review_service.log") as mock_log:
            sources = await _run_ingestion_pipeline(mock_db_session, profile_all_sources)

        assert len(sources) == 3
        assert mock_db_session.add.call_count == 3
        mock_log.error.assert_not_called()

    @pytest.mark.asyncio
    async def test_stores_raw_data_as_json(
        self, mock_db_session: AsyncMock, profile_all_sources: Mock
    ) -> None:
        """Each persisted IngestedSource carries its source data as JSON."""
        await _run_ingestion_pipeline(mock_db_session, profile_all_sources)

        persisted = [call.args[0] for call in mock_db_session.add.call_args_list]
        resume_record = next(p for p in persisted if p.source_type == "resume")

        assert json.loads(resume_record.raw_data) == {
            "source_type": "resume",
            "filename": "resume.pdf",
            "data": "Experienced software engineer.",
        }

    @pytest.mark.asyncio
    async def test_skips_missing_sources(self, mock_db_session: AsyncMock) -> None:
        """A profile with no ingestible sources persists nothing."""
        profile = Mock()
        profile.id = uuid4()
        profile.github_username = None
        profile.portfolio_url = None
        profile.resume_text = None

        sources = await _run_ingestion_pipeline(mock_db_session, profile)

        assert sources == []
        mock_db_session.add.assert_not_called()
