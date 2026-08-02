"""Tests for web_parser.py"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.web_parser import WebParser

if TYPE_CHECKING:
    from pytest_httpserver import HTTPServer

SAMPLE_PORTFOLIO_HTML = """
<html>
  <head><title>Jane Doe — Portfolio</title></head>
  <body>
    <nav>Home About Projects Contact</nav>
    <header><h1>Jane Doe</h1></header>
    <main>
      <p>I am a backend engineer who loves building APIs.</p>
      <h2>Projects</h2>
      <p>PortfolioTracker: a Django app with tests and CI.</p>
    </main>
    <footer>Copyright 2026 Jane Doe</footer>
    <script>console.log("analytics");</script>
    <style>body { color: red; }</style>
  </body>
</html>
"""


@pytest.mark.unit
class TestWebParser:
    """Test suite for WebParser."""

    @pytest.fixture
    def parser(self) -> WebParser:
        """Create a WebParser instance."""
        return WebParser()

    def test_parse_extracts_readable_text(self, parser: WebParser) -> None:
        """Test that visible portfolio copy is extracted."""
        result = parser.parse(SAMPLE_PORTFOLIO_HTML)

        assert isinstance(result, ParseResult)
        assert result.source_type == "portfolio"
        assert result.metadata["source_type"] == "portfolio"
        assert "backend engineer" in result.text
        assert "PortfolioTracker" in result.text

    def test_parse_drops_noise_tags(self, parser: WebParser) -> None:
        """Test that script, style, nav, and footer content is removed."""
        result = parser.parse(SAMPLE_PORTFOLIO_HTML)

        assert "analytics" not in result.text  # <script>
        assert "color: red" not in result.text  # <style>
        assert "Home About Projects Contact" not in result.text  # <nav>
        assert "Copyright" not in result.text  # <footer>

    def test_parse_extracts_metadata(self, parser: WebParser) -> None:
        """Test that title and word count are captured."""
        result = parser.parse(SAMPLE_PORTFOLIO_HTML)

        assert result.metadata["title"] == "Jane Doe — Portfolio"
        assert result.metadata["word_count"] > 0

    def test_parse_accepts_bytes(self, parser: WebParser) -> None:
        """Test that HTML supplied as bytes is decoded and parsed."""
        result = parser.parse(SAMPLE_PORTFOLIO_HTML.encode("utf-8"))

        assert isinstance(result, ParseResult)
        assert "backend engineer" in result.text

    def test_parse_invalid_content_type(self, parser: WebParser) -> None:
        """Test that non-string/bytes content raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)  # type: ignore[arg-type]

        assert "Content must be" in str(exc_info.value)

    def test_parse_empty_page_raises(self, parser: WebParser) -> None:
        """Test that HTML with no readable text raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse("<html><body><script>x=1</script></body></html>")

        assert "No readable text" in str(exc_info.value)

    def test_fetch_returns_html(self, parser: WebParser, httpserver: HTTPServer) -> None:
        """Test that fetch downloads a page served over HTTP."""
        httpserver.expect_request("/portfolio").respond_with_data(
            SAMPLE_PORTFOLIO_HTML, content_type="text/html"
        )

        html = parser.fetch(httpserver.url_for("/portfolio"))

        assert "Jane Doe" in html

    def test_fetch_rejects_non_http_scheme(self, parser: WebParser) -> None:
        """Test that a non-http(s) URL raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.fetch("ftp://example.com/site")

        assert "http" in str(exc_info.value)

    def test_fetch_rejects_non_html(self, parser: WebParser, httpserver: HTTPServer) -> None:
        """Test that a non-HTML response raises ValueError."""
        httpserver.expect_request("/data").respond_with_json({"hello": "world"})

        with pytest.raises(ValueError) as exc_info:
            parser.fetch(httpserver.url_for("/data"))

        assert "HTML" in str(exc_info.value)

    def test_fetch_rejects_error_status(self, parser: WebParser, httpserver: HTTPServer) -> None:
        """Test that an error status code raises ValueError."""
        httpserver.expect_request("/missing").respond_with_data("nope", status=404)

        with pytest.raises(ValueError) as exc_info:
            parser.fetch(httpserver.url_for("/missing"))

        assert "Failed to fetch" in str(exc_info.value)
