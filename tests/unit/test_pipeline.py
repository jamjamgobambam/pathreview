"""Tests for pipeline.py"""

from unittest.mock import Mock

import pytest

from ingestion.chunking.base import Chunk
from ingestion.parsers.base import ParseResult
from ingestion.pipeline import IngestionPipeline, IngestResult


@pytest.mark.unit
class TestIngestPortfolio:
    """Test suite for IngestionPipeline.ingest_portfolio."""

    @pytest.fixture
    def pipeline(self):
        """Create an IngestionPipeline with mocked collaborators."""
        vector_db = Mock()
        db_session = Mock()
        embedding_provider = Mock()
        return IngestionPipeline(vector_db, db_session, embedding_provider)

    def test_ingest_portfolio_success(self, pipeline):
        """Test a successful portfolio ingestion parses, chunks, embeds, and records."""
        pipeline.web_parser.parse = Mock(
            return_value=ParseResult(
                text="Jane Doe builds things with Python.",
                metadata={"source_type": "portfolio", "url": "http://example.com", "word_count": 6},
                source_type="portfolio",
            )
        )
        fake_chunks = [Chunk(text="Jane Doe builds things with Python.", metadata={})]
        pipeline.strategy_selector.chunk = Mock(return_value=fake_chunks)
        pipeline.batch_processor.process = Mock(return_value=[(fake_chunks[0], "embed-id-1")])
        pipeline._check_skip = Mock(return_value=None)
        pipeline._record_ingested_source = Mock()

        result = pipeline.ingest_portfolio("profile-1", "http://example.com")

        assert isinstance(result, IngestResult)
        assert result.skipped is False
        assert result.chunk_count == 1
        pipeline.web_parser.parse.assert_called_once_with("http://example.com")
        pipeline.strategy_selector.chunk.assert_called_once()
        pipeline.batch_processor.process.assert_called_once_with(fake_chunks)
        pipeline._record_ingested_source.assert_called_once()

    def test_ingest_portfolio_skips_when_already_ingested(self, pipeline):
        """Test that a duplicate source_id is skipped without re-fetching."""
        skip_result = IngestResult(
            source_id="portfolio_profile-1_abc123",
            chunk_count=0,
            skipped=True,
            skip_reason="Source already ingested",
        )
        pipeline._check_skip = Mock(return_value=skip_result)
        pipeline.web_parser.parse = Mock()

        result = pipeline.ingest_portfolio("profile-1", "http://example.com")

        assert result.skipped is True
        pipeline.web_parser.parse.assert_not_called()

    def test_ingest_portfolio_propagates_parse_failures(self, pipeline):
        """Test that a parse failure (e.g. unreachable URL) raises instead of succeeding."""
        pipeline._check_skip = Mock(return_value=None)
        pipeline.web_parser.parse = Mock(side_effect=ValueError("Failed to fetch portfolio URL"))

        with pytest.raises(ValueError):
            pipeline.ingest_portfolio("profile-1", "http://unreachable.example.com")
