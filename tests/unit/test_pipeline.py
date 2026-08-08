"""Tests for ingestion/pipeline.py"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ingestion.embeddings.provider import MockEmbeddingProvider
from ingestion.parsers.base import ParseResult
from ingestion.pipeline import IngestionPipeline, IngestResult


@pytest.mark.unit
class TestIngestPortfolioUrl:
    """Test suite for IngestionPipeline.ingest_portfolio_url."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session with no existing sources."""
        session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        session.execute = AsyncMock(return_value=result)
        session.add = Mock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def pipeline(self, mock_db_session):
        """Create an IngestionPipeline with a mock vector DB and db session."""
        vector_db = MagicMock()
        return IngestionPipeline(
            vector_db=vector_db,
            db_session=mock_db_session,
            embedding_provider=MockEmbeddingProvider(),
        )

    @pytest.mark.asyncio
    async def test_ingest_portfolio_url_happy_path(self, pipeline, mock_db_session):
        """Test successful ingestion produces chunks and records the source."""
        parse_result = ParseResult(
            text="Jane Doe is a software engineer who builds web applications. "
            "She has experience with Python and React.",
            metadata={
                "source_type": "web",
                "url": "https://jane.dev",
                "title": "Jane Doe",
                "word_count": 15,
            },
            source_type="web",
        )

        with patch.object(pipeline.web_parser, "fetch_and_parse", return_value=parse_result):
            result = await pipeline.ingest_portfolio_url(
                profile_id="profile-123", url="https://jane.dev"
            )

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.chunk_count > 0
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_awaited_once()

        added_source = mock_db_session.add.call_args[0][0]
        assert added_source.source_type == "web"
        assert added_source.source_url == "https://jane.dev"
        assert added_source.profile_id == "profile-123"
        assert added_source.chunk_count == result.chunk_count

    @pytest.mark.asyncio
    async def test_ingest_portfolio_url_skips_if_already_ingested(self, pipeline, mock_db_session):
        """Test that re-ingesting unchanged content is a no-op via content-hash dedup."""
        existing_source = Mock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = existing_source
        mock_db_session.execute = AsyncMock(return_value=result_mock)

        parse_result = ParseResult(
            text="Same content every time.",
            metadata={
                "source_type": "web",
                "url": "https://jane.dev",
                "title": "",
                "word_count": 4,
            },
            source_type="web",
        )

        with patch.object(pipeline.web_parser, "fetch_and_parse", return_value=parse_result):
            result = await pipeline.ingest_portfolio_url(
                profile_id="profile-123", url="https://jane.dev"
            )

        assert result.skipped is True
        assert result.chunk_count == 0
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingest_portfolio_url_propagates_fetch_failure(self, pipeline):
        """Test that an unreachable/erroring URL raises rather than being swallowed silently."""
        with (
            patch.object(pipeline.web_parser, "fetch_and_parse", side_effect=ValueError("boom")),
            pytest.raises(ValueError),
        ):
            await pipeline.ingest_portfolio_url(profile_id="profile-123", url="https://down.dev")

    @pytest.mark.asyncio
    async def test_ingest_portfolio_url_no_extractable_text(self, pipeline, mock_db_session):
        """Test a page with no extractable text produces zero chunks without erroring."""
        parse_result = ParseResult(
            text="",
            metadata={"source_type": "web", "url": "https://spa.dev", "title": "", "word_count": 0},
            source_type="web",
        )

        with patch.object(pipeline.web_parser, "fetch_and_parse", return_value=parse_result):
            result = await pipeline.ingest_portfolio_url(
                profile_id="profile-123", url="https://spa.dev"
            )

        assert result.skipped is False
        assert result.chunk_count == 0
