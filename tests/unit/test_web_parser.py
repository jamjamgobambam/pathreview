"""Tests for web_parser.py"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.web_parser import WebParser


@pytest.mark.unit
class TestWebParser:
    """Test suite for WebParser."""

    @pytest.fixture
    def parser(self) -> WebParser:
        """Create a WebParser instance."""
        return WebParser()

    @patch("ingestion.parsers.web_parser.httpx.get")
    def test_parse_valid_url(self, mock_get: MagicMock, parser: WebParser) -> None:
        """Test parsing a valid URL with HTML content."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = (
            "<html><head><title>My Portfolio</title></head><body><h1>Hello</h1>"
            "<p>I am a developer.</p><nav>Menu</nav><script>alert(1)</script></body></html>"
        )
        mock_get.return_value = mock_response

        result = parser.parse("http://example.com/portfolio")

        assert isinstance(result, ParseResult)
        assert "Hello" in result.text
        assert "I am a developer." in result.text
        assert "Menu" not in result.text  # stripped out
        assert "alert(1)" not in result.text  # stripped out
        assert result.metadata["title"] == "My Portfolio"
        assert result.metadata["source_url"] == "http://example.com/portfolio"
        assert result.source_type == "portfolio"

    def test_parse_invalid_content_type(self, parser: WebParser) -> None:
        """Test that invalid content type raises ValueError."""
        with pytest.raises(ValueError, match="WebParser expects a URL string as content"):
            parser.parse(12345)  # type: ignore

    def test_parse_invalid_url_format(self, parser: WebParser) -> None:
        """Test that invalid URL format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL: invalid-url"):
            parser.parse("invalid-url")

    @patch("ingestion.parsers.web_parser.httpx.get")
    def test_parse_http_error(self, mock_get: MagicMock, parser: WebParser) -> None:
        """Test handling HTTP errors during fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        mock_get.side_effect = error

        with pytest.raises(ValueError, match="HTTP error fetching portfolio URL: 404"):
            parser.parse("http://example.com/not-found")
