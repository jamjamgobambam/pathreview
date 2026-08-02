"""Tests for the portfolio path of pipeline.py"""

from typing import NamedTuple
from unittest.mock import MagicMock

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.pipeline import IngestionPipeline, IngestResult


class PortfolioHarness(NamedTuple):
    """A pipeline plus handles to its mocked collaborators for assertions."""

    pipeline: IngestionPipeline
    web_parser: MagicMock
    strategy_selector: MagicMock
    batch_processor: MagicMock
    db_session: MagicMock


@pytest.mark.unit
class TestIngestPortfolio:
    """Test suite for IngestionPipeline.ingest_portfolio."""

    @pytest.fixture
    def harness(self) -> PortfolioHarness:
        """Create a pipeline with mocked collaborators (no network or DB)."""
        db_session = MagicMock()
        # Default: nothing has been ingested yet, so ingestion proceeds.
        db_session.query.return_value.filter_by.return_value.first.return_value = None

        pipeline = IngestionPipeline(
            vector_db=MagicMock(),
            db_session=db_session,
            embedding_provider=MagicMock(),
        )

        # Replace collaborators so the test does no network, DB, or embedding work.
        web_parser = MagicMock()
        web_parser.fetch.return_value = "<html><body>portfolio</body></html>"
        web_parser.parse.return_value = ParseResult(
            text="I am a backend engineer.",
            metadata={"source_type": "portfolio", "title": "Jane Doe", "word_count": 5},
            source_type="portfolio",
        )
        pipeline.web_parser = web_parser

        strategy_selector = MagicMock()
        strategy_selector.chunk.return_value = ["chunk-1", "chunk-2"]
        pipeline.strategy_selector = strategy_selector

        batch_processor = MagicMock()
        pipeline.batch_processor = batch_processor

        return PortfolioHarness(
            pipeline, web_parser, strategy_selector, batch_processor, db_session
        )

    def test_ingest_portfolio_success(self, harness: PortfolioHarness) -> None:
        """Test that a portfolio URL is fetched, chunked, and stored."""
        result = harness.pipeline.ingest_portfolio("profile-123", "https://jane.dev")

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.chunk_count == 2
        assert result.source_id.startswith("portfolio_profile-123_")
        harness.web_parser.fetch.assert_called_once_with("https://jane.dev")
        harness.batch_processor.process.assert_called_once()

    def test_ingest_portfolio_passes_url_in_metadata(self, harness: PortfolioHarness) -> None:
        """Test that the portfolio URL is recorded in the chunk metadata."""
        harness.pipeline.ingest_portfolio("profile-123", "https://jane.dev")

        _text, metadata = harness.strategy_selector.chunk.call_args.args
        assert metadata["url"] == "https://jane.dev"
        assert metadata["source_type"] == "portfolio"

    def test_ingest_portfolio_skips_already_ingested(self, harness: PortfolioHarness) -> None:
        """Test that an already-ingested portfolio is skipped."""
        harness.db_session.query.return_value.filter_by.return_value.first.return_value = object()

        result = harness.pipeline.ingest_portfolio("profile-123", "https://jane.dev")

        assert result.skipped is True
        harness.web_parser.fetch.assert_not_called()

    def test_ingest_portfolio_propagates_fetch_error(self, harness: PortfolioHarness) -> None:
        """Test that a fetch failure is raised, not swallowed."""
        harness.web_parser.fetch.side_effect = ValueError("unreachable")

        with pytest.raises(ValueError):
            harness.pipeline.ingest_portfolio("profile-123", "https://jane.dev")
