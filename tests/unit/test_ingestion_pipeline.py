"""Tests for portfolio website ingestion."""

from email.message import Message
from typing import Any, cast
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.pipeline import IngestionPipeline


@pytest.mark.unit
class TestPortfolioIngestion:
    """Test suite for portfolio website ingestion."""

    @pytest.fixture
    def pipeline(self) -> Any:
        """Create an ingestion pipeline with mocked dependencies."""
        pipeline = IngestionPipeline(
            vector_db=Mock(),
            db_session=Mock(),
            embedding_provider=Mock(),
        )

        mock_pipeline = cast(Any, pipeline)

        mock_pipeline.web_parser = Mock()
        mock_pipeline.strategy_selector = Mock()
        mock_pipeline.batch_processor = Mock()
        mock_pipeline._check_skip = Mock(return_value=None)
        mock_pipeline._record_ingested_source = Mock()

        return mock_pipeline

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_success(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test successful portfolio fetching, parsing, and ingestion."""
        html = b"""
        <html>
            <head><title>Jane Doe Portfolio</title></head>
            <body>
                <h1>Jane Doe</h1>
                <p>Software engineer building AI applications.</p>
            </body>
        </html>
        """

        response = MagicMock()
        response.read.return_value = html
        response.headers.get_content_type.return_value = "text/html"
        mock_urlopen.return_value.__enter__.return_value = response

        parse_result = ParseResult(
            text="Jane Doe Software engineer building AI applications.",
            metadata={
                "source_type": "web",
                "title": "Jane Doe Portfolio",
                "word_count": 7,
            },
            source_type="web",
        )
        pipeline.web_parser.parse.return_value = parse_result

        chunks = [Mock(), Mock()]
        pipeline.strategy_selector.chunk.return_value = chunks

        result = pipeline.ingest_portfolio(
            profile_id="profile-123",
            portfolio_url="https://example.com",
        )

        mock_urlopen.assert_called_once()
        pipeline.web_parser.parse.assert_called_once_with(html)

        pipeline.strategy_selector.chunk.assert_called_once()
        chunk_text, metadata = pipeline.strategy_selector.chunk.call_args.args

        assert chunk_text == parse_result.text
        assert metadata["profile_id"] == "profile-123"
        assert metadata["portfolio_url"] == "https://example.com"
        assert metadata["source_type"] == "web"
        assert metadata["title"] == "Jane Doe Portfolio"
        assert metadata["source_id"].startswith("portfolio_profile-123_")

        pipeline.batch_processor.process.assert_called_once_with(chunks)

        pipeline._record_ingested_source.assert_called_once_with(
            result.source_id,
            "portfolio",
            "profile-123",
            2,
        )

        assert result.chunk_count == 2
        assert result.skipped is False
        assert result.source_id.startswith("portfolio_profile-123_")

    def test_ingest_portfolio_rejects_invalid_url(
        self,
        pipeline: Any,
    ) -> None:
        """Test that non-HTTP portfolio URLs are rejected."""
        with pytest.raises(
            ValueError,
            match="valid HTTP or HTTPS URL",
        ):
            pipeline.ingest_portfolio(
                profile_id="profile-123",
                portfolio_url="not-a-valid-url",
            )

        pipeline.web_parser.parse.assert_not_called()
        pipeline.batch_processor.process.assert_not_called()

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_handles_connection_failure(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test that connection failures produce a clear error."""
        mock_urlopen.side_effect = URLError("Connection refused")

        with pytest.raises(
            RuntimeError,
            match="could not be reached",
        ):
            pipeline.ingest_portfolio(
                profile_id="profile-123",
                portfolio_url="https://example.com",
            )

        pipeline.web_parser.parse.assert_not_called()
        pipeline.batch_processor.process.assert_not_called()

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_handles_timeout(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test that request timeouts are handled gracefully."""
        mock_urlopen.side_effect = URLError(TimeoutError("Request timed out"))

        with pytest.raises(
            RuntimeError,
            match="could not be reached",
        ):
            pipeline.ingest_portfolio(
                profile_id="profile-123",
                portfolio_url="https://example.com",
            )

        pipeline.web_parser.parse.assert_not_called()
        pipeline.batch_processor.process.assert_not_called()

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_rejects_non_html_response(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test that non-HTML portfolio responses are rejected."""
        response = MagicMock()
        response.headers.get_content_type.return_value = "application/pdf"
        mock_urlopen.return_value.__enter__.return_value = response

        with pytest.raises(
            ValueError,
            match="must return HTML",
        ):
            pipeline.ingest_portfolio(
                profile_id="profile-123",
                portfolio_url="https://example.com/portfolio.pdf",
            )

        pipeline.web_parser.parse.assert_not_called()
        pipeline.batch_processor.process.assert_not_called()

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_rejects_empty_page(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test that pages with no readable content are rejected."""
        response = MagicMock()
        response.read.return_value = b"<html><body></body></html>"
        response.headers.get_content_type.return_value = "text/html"
        mock_urlopen.return_value.__enter__.return_value = response

        pipeline.web_parser.parse.return_value = ParseResult(
            text="",
            metadata={
                "source_type": "web",
                "title": "",
                "word_count": 0,
            },
            source_type="web",
        )

        with pytest.raises(
            ValueError,
            match="no readable text",
        ):
            pipeline.ingest_portfolio(
                profile_id="profile-123",
                portfolio_url="https://example.com",
            )

        pipeline.batch_processor.process.assert_not_called()
        pipeline._record_ingested_source.assert_not_called()

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_handles_http_error(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test that unsuccessful HTTP responses are handled."""
        mock_urlopen.side_effect = HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs=Message(),
            fp=None,
        )

        with pytest.raises(
            RuntimeError,
            match="HTTP status 404",
        ):
            pipeline.ingest_portfolio(
                profile_id="profile-123",
                portfolio_url="https://example.com",
            )

        pipeline.web_parser.parse.assert_not_called()
        pipeline.batch_processor.process.assert_not_called()

    @patch("ingestion.pipeline.urlopen")
    def test_ingest_portfolio_skips_duplicate_source(
        self,
        mock_urlopen: Mock,
        pipeline: Any,
    ) -> None:
        """Test that previously ingested portfolio content is skipped."""
        response = MagicMock()
        response.read.return_value = b"<html><body>Portfolio</body></html>"
        response.headers.get_content_type.return_value = "text/html"
        mock_urlopen.return_value.__enter__.return_value = response

        skipped_result = Mock(
            source_id="portfolio_profile-123_existing",
            chunk_count=0,
            skipped=True,
            skip_reason="Source already ingested",
        )
        pipeline._check_skip.return_value = skipped_result

        result = pipeline.ingest_portfolio(
            profile_id="profile-123",
            portfolio_url="https://example.com",
        )

        assert result is skipped_result
        pipeline.web_parser.parse.assert_not_called()
        pipeline.batch_processor.process.assert_not_called()
