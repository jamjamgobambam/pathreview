"""Tests for web_parser.py and IngestionPipeline.ingest_portfolio."""

from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.web_parser import WebParser


@pytest.mark.unit
class TestWebParser:
    """Test suite for WebParser."""

    @pytest.fixture
    def parser(self):
        """Create a WebParser instance."""
        return WebParser()

    def test_parse_portfolio_page_html(self, parser):
        """Parsing a portfolio page's HTML should extract bio/project text."""
        sample_html = """
        <html>
          <body>
            <h1>Jane Doe</h1>
            <p>Software engineer building web apps.</p>
            <section id="projects">
              <h2>Weather App</h2>
              <p>A weather forecasting app built with React.</p>
            </section>
          </body>
        </html>
        """

        result = parser.parse(sample_html)

        assert isinstance(result, ParseResult)
        assert result.source_type == "web"
        assert "Jane Doe" in result.text
        assert "Weather App" in result.text

    def test_parse_strips_script_and_style_boilerplate(self, parser):
        """Script, style, and nav content should not appear in extracted text."""
        html = """
        <html>
          <head><style>body { color: red; }</style></head>
          <body>
            <nav>Home About Contact</nav>
            <script>console.log("tracking");</script>
            <p>Real portfolio content.</p>
          </body>
        </html>
        """

        result = parser.parse(html)

        assert "Real portfolio content" in result.text
        assert "console.log" not in result.text
        assert "color: red" not in result.text
        assert "Home About Contact" not in result.text

    def test_parse_extracts_title_metadata(self, parser):
        """The page <title> should be captured in metadata."""
        html = "<html><head><title>Jane Doe - Portfolio</title></head><body><p>Hi</p></body></html>"

        result = parser.parse(html)

        assert result.metadata["title"] == "Jane Doe - Portfolio"

    def test_parse_no_title_returns_none(self, parser):
        """Missing <title> should not raise, just leave metadata title as None."""
        html = "<html><body><p>No title here</p></body></html>"

        result = parser.parse(html)

        assert result.metadata["title"] is None

    def test_parse_word_count_metadata(self, parser):
        """Word count should reflect the extracted text, not the raw HTML."""
        html = "<html><body><p>One two three four five</p></body></html>"

        result = parser.parse(html)

        assert result.metadata["word_count"] == 5

    def test_parse_bytes_input(self, parser):
        """Bytes input should be decoded before parsing."""
        html_bytes = b"<html><body><p>Bytes portfolio content</p></body></html>"

        result = parser.parse(html_bytes)

        assert isinstance(result, ParseResult)
        assert "Bytes portfolio content" in result.text

    def test_parse_invalid_content_type(self, parser):
        """Non-str/bytes content should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)

        assert "Content must be" in str(exc_info.value)

    def test_fetch_success(self, parser):
        """A successful fetch should return the response's HTML text."""
        mock_response = Mock()
        mock_response.text = "<html><body><p>Fetched</p></body></html>"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = Mock()

        with patch(
            "ingestion.parsers.web_parser.httpx.get", return_value=mock_response
        ) as mock_get:
            html = parser.fetch("https://example.com/portfolio")

        mock_get.assert_called_once()
        assert html == "<html><body><p>Fetched</p></body></html>"

    def test_fetch_http_error_raises_value_error(self, parser):
        """HTTP errors (timeouts, connection errors, 4xx/5xx) should raise ValueError."""
        with patch(
            "ingestion.parsers.web_parser.httpx.get",
            side_effect=httpx.ConnectTimeout("timed out"),
        ), pytest.raises(ValueError) as exc_info:
            parser.fetch("https://example.com/portfolio")

        assert "Failed to fetch" in str(exc_info.value)

    def test_fetch_non_html_content_type_raises_value_error(self, parser):
        """A non-HTML response (e.g. a PDF) should raise ValueError."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.raise_for_status = Mock()

        with (
            patch("ingestion.parsers.web_parser.httpx.get", return_value=mock_response),
            pytest.raises(ValueError) as exc_info,
        ):
            parser.fetch("https://example.com/resume.pdf")

        assert "Unsupported content type" in str(exc_info.value)


@pytest.mark.unit
class TestIngestionPipelinePortfolio:
    """The pipeline should be able to ingest a portfolio URL end-to-end."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock db session with no existing ingested sources."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        return session

    @pytest.fixture
    def mock_embedding_provider(self):
        provider = Mock()
        provider.embed = Mock(return_value=[[0.1] * 1536])
        return provider

    @pytest.fixture
    def mock_vector_db(self):
        return Mock()

    @pytest.fixture
    def pipeline(self, mock_vector_db, mock_db_session, mock_embedding_provider):
        from ingestion.pipeline import IngestionPipeline

        return IngestionPipeline(
            vector_db=mock_vector_db,
            db_session=mock_db_session,
            embedding_provider=mock_embedding_provider,
        )

    def test_ingest_portfolio_method_exists(self):
        """IngestionPipeline should expose an ingest_portfolio method."""
        from ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline(vector_db=None, db_session=None, embedding_provider=None)

        assert hasattr(pipeline, "ingest_portfolio")

    def test_ingest_portfolio_success(self, pipeline, mock_db_session):
        """A fresh portfolio URL should be fetched, parsed, chunked, embedded, and recorded."""
        sample_html = "<html><body><h1>Jane Doe</h1><p>Building things.</p></body></html>"

        with patch.object(pipeline.web_parser, "fetch", return_value=sample_html):
            result = pipeline.ingest_portfolio(profile_id="profile-1", url="https://janedoe.dev")

        assert result.skipped is False
        assert result.chunk_count > 0
        assert result.source_id.startswith("web_profile-1_")
        # Recorded in the DB for future dedup
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        recorded = mock_db_session.add.call_args[0][0]
        assert recorded.profile_id == "profile-1"
        assert recorded.source_type == "web"
        assert recorded.source_url == "https://janedoe.dev"

    def test_ingest_portfolio_skips_when_already_ingested(
        self, pipeline, mock_db_session
    ):
        """The same portfolio content should not be re-embedded."""
        sample_html = "<html><body><p>Same content every time</p></body></html>"

        existing = Mock()
        existing.id = "existing-source-id"
        existing.chunk_count = 3
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = existing

        with patch.object(pipeline.web_parser, "fetch", return_value=sample_html):
            result = pipeline.ingest_portfolio(profile_id="profile-1", url="https://janedoe.dev")

        assert result.skipped is True
        assert result.skip_reason == "Source already ingested"
        assert result.chunk_count == 3
        mock_db_session.add.assert_not_called()

    def test_ingest_portfolio_fetch_failure_propagates(self, pipeline):
        """An unreachable portfolio URL should raise so the caller can decide how to handle it."""
        with (
            patch.object(
                pipeline.web_parser,
                "fetch",
                side_effect=ValueError("Failed to fetch https://down.example"),
            ),
            pytest.raises(ValueError),
        ):
            pipeline.ingest_portfolio(profile_id="profile-1", url="https://down.example")
