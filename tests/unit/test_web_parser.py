"""Tests for web_parser.py"""

from unittest.mock import Mock, patch

import httpx
import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.web_parser import WebParser


def _mock_response(text: str, status_code: int = 200, content_type: str = "text/html"):
    response = Mock()
    response.status_code = status_code
    response.headers = {"content-type": content_type}
    response.text = text
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=Mock(), response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


@pytest.mark.unit
class TestWebParser:
    """Test suite for WebParser."""

    @pytest.fixture
    def parser(self):
        """Create a WebParser instance."""
        return WebParser()

    def test_parse_extracts_visible_text_and_title(self, parser):
        """Test parsing a simple HTML page extracts body text and title."""
        html = """
        <html>
          <head><title>Jane Doe Portfolio</title></head>
          <body>
            <h1>Jane Doe</h1>
            <p>I build things with Python and React.</p>
          </body>
        </html>
        """
        with patch("ingestion.parsers.web_parser.httpx.get", return_value=_mock_response(html)):
            result = parser.parse("http://example.com")

        assert isinstance(result, ParseResult)
        assert result.source_type == "portfolio"
        assert "Jane Doe" in result.text
        assert "I build things with Python and React." in result.text
        assert result.metadata["title"] == "Jane Doe Portfolio"
        assert result.metadata["url"] == "http://example.com"
        assert result.metadata["word_count"] > 0

    def test_parse_strips_script_and_style_tags(self, parser):
        """Test that script/style content never ends up in extracted text."""
        html = """
        <html><body>
          <script>console.log('should not appear')</script>
          <style>.hidden { display: none; }</style>
          <p>Real visible content</p>
        </body></html>
        """
        with patch("ingestion.parsers.web_parser.httpx.get", return_value=_mock_response(html)):
            result = parser.parse("http://example.com")

        assert "should not appear" not in result.text
        assert "display: none" not in result.text
        assert "Real visible content" in result.text

    def test_parse_empty_url_raises_value_error(self, parser):
        """Test that an empty string is rejected before any request is made."""
        with pytest.raises(ValueError):
            parser.parse("")

    def test_parse_non_string_content_raises_value_error(self, parser):
        """Test that non-string content is rejected."""
        with pytest.raises(ValueError):
            parser.parse(b"not-a-url")

    def test_parse_non_200_status_raises_value_error(self, parser):
        """Test that a 404 response surfaces as a ValueError, not a raw httpx exception."""
        with (
            patch(
                "ingestion.parsers.web_parser.httpx.get",
                return_value=_mock_response("<html></html>", status_code=404),
            ),
            pytest.raises(ValueError, match="404"),
        ):
            parser.parse("http://example.com/missing")

    def test_parse_unreachable_url_raises_value_error(self, parser):
        """Test that a connection failure surfaces as a ValueError."""
        with (
            patch(
                "ingestion.parsers.web_parser.httpx.get",
                side_effect=httpx.ConnectError("connection refused"),
            ),
            pytest.raises(ValueError),
        ):
            parser.parse("http://localhost:9999")

    def test_parse_non_html_content_type_raises_value_error(self, parser):
        """Test that a non-HTML response (e.g. a PDF) is rejected."""
        with (
            patch(
                "ingestion.parsers.web_parser.httpx.get",
                return_value=_mock_response("%PDF-1.4", content_type="application/pdf"),
            ),
            pytest.raises(ValueError, match="HTML"),
        ):
            parser.parse("http://example.com/resume.pdf")

    def test_parse_empty_page_returns_low_signal_result_without_crashing(self, parser):
        """Test that a JS-only empty shell produces a valid but low-signal ParseResult."""
        html = "<html><body><div id='root'></div></body></html>"
        with patch("ingestion.parsers.web_parser.httpx.get", return_value=_mock_response(html)):
            result = parser.parse("http://example.com/spa")

        assert isinstance(result, ParseResult)
        assert result.text == ""
        assert result.metadata["word_count"] == 0
