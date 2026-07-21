"""Tests for web_parser.py"""

from unittest.mock import Mock, patch

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

    def test_parse_extracts_visible_text_and_title(self, parser):
        """Test parsing a website URL extracts page text and title."""
        html = """
        <html>
            <head>
                <title>Jane Doe Portfolio</title>
                <script>console.log('ignore me')</script>
            </head>
            <body>
                <h1>Jane Doe</h1>
                <p>Backend engineer building AI tools.</p>
                <style>body { color: red; }</style>
            </body>
        </html>
        """

        response = Mock(spec=httpx.Response)
        response.text = html
        response.raise_for_status = Mock()

        with patch("ingestion.parsers.web_parser.httpx.get", return_value=response) as mock_get:
            result = parser.parse("https://example.com")

        assert isinstance(result, ParseResult)
        assert result.source_type == "web"
        assert result.metadata["source_type"] == "web"
        assert result.metadata["url"] == "https://example.com"
        assert result.metadata["title"] == "Jane Doe Portfolio"
        assert result.metadata["word_count"] > 0
        assert result.metadata["content_hash"]
        assert "Jane Doe" in result.text
        assert "Backend engineer" in result.text
        assert "console.log" not in result.text
        mock_get.assert_called_once_with("https://example.com", follow_redirects=True, timeout=10.0)

    def test_parse_accepts_bytes_url(self, parser):
        """Test parsing accepts URL bytes input."""
        response = Mock(spec=httpx.Response)
        response.text = "<html><head><title>Portfolio</title></head><body>Hello</body></html>"
        response.raise_for_status = Mock()

        with patch("ingestion.parsers.web_parser.httpx.get", return_value=response):
            result = parser.parse(b"https://portfolio.example")

        assert result.metadata["url"] == "https://portfolio.example"
        assert result.text == "Hello"

    def test_parse_invalid_url_raises_value_error(self, parser):
        """Test invalid URL formats raise ValueError."""
        with pytest.raises(ValueError):
            parser.parse("not-a-url")

    def test_parse_non_string_content_raises_value_error(self, parser):
        """Test unsupported input types raise ValueError."""
        with pytest.raises(ValueError):
            parser.parse(12345)

    def test_http_error_propagates(self, parser):
        """Test HTTP errors from the fetch step propagate."""
        response = Mock(spec=httpx.Response)
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "boom",
            request=Mock(),
            response=Mock(status_code=500),
        )

        with patch("ingestion.parsers.web_parser.httpx.get", return_value=response):
            with pytest.raises(httpx.HTTPStatusError):
                parser.parse("https://example.com")