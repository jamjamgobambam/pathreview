"""Tests for web_page_parser.py"""

import httpx
import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.web_page_parser import WebPageParser


@pytest.mark.unit
class TestWebPageParser:
    """Test suite for WebPageParser."""

    @pytest.fixture
    def parser(self):
        """Create a WebPageParser instance."""
        return WebPageParser()

    def test_parse_strips_scripts_and_styles(self, parser):
        """Test that script/style/nav/footer tags are stripped from extracted text."""
        html = """
        <html>
          <head><title>My Portfolio</title></head>
          <body>
            <nav>Home | About</nav>
            <script>trackVisit();</script>
            <style>body { color: red; }</style>
            <main>
              <h1>Jane Doe</h1>
              <p>Software engineer building things.</p>
            </main>
            <footer>Copyright 2026</footer>
          </body>
        </html>
        """
        result = parser.parse(html, url="https://jane.dev")

        assert isinstance(result, ParseResult)
        assert result.source_type == "web"
        assert result.metadata["source_type"] == "web"
        assert result.metadata["url"] == "https://jane.dev"
        assert result.metadata["title"] == "My Portfolio"
        assert "Jane Doe" in result.text
        assert "Software engineer" in result.text
        assert "trackVisit" not in result.text
        assert "color: red" not in result.text
        assert "Home | About" not in result.text
        assert "Copyright 2026" not in result.text

    def test_parse_empty_html_produces_empty_text(self, parser):
        """Test that a near-empty page (e.g. an unrendered SPA shell) doesn't crash."""
        html = "<html><head></head><body><div id='root'></div></body></html>"
        result = parser.parse(html, url="https://spa.dev")

        assert isinstance(result, ParseResult)
        assert result.text == ""
        assert result.metadata["word_count"] == 0

    def test_parse_bytes_input(self, parser):
        """Test parsing HTML from bytes input."""
        html_bytes = b"<html><body><p>Hello world</p></body></html>"
        result = parser.parse(html_bytes, url="https://example.dev")

        assert isinstance(result, ParseResult)
        assert "Hello world" in result.text

    def test_parse_invalid_content_type(self, parser):
        """Test that invalid content type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)

        assert "Content must be a string or bytes" in str(exc_info.value)

    def test_parse_no_title(self, parser):
        """Test parsing a page with no <title> tag doesn't crash."""
        html = "<html><body><p>No title here</p></body></html>"
        result = parser.parse(html, url="https://notitle.dev")

        assert result.metadata["title"] == ""

    def test_fetch_and_parse_success(self, parser, monkeypatch):
        """Test fetch_and_parse on a successful HTML response."""

        def fake_get(url, timeout=None, follow_redirects=None):
            return httpx.Response(
                status_code=200,
                headers={"content-type": "text/html; charset=utf-8"},
                text="<html><body><p>Portfolio content</p></body></html>",
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        result = parser.fetch_and_parse("https://someone.dev")

        assert isinstance(result, ParseResult)
        assert "Portfolio content" in result.text
        assert result.metadata["url"] == "https://someone.dev"

    def test_fetch_and_parse_http_error(self, parser, monkeypatch):
        """Test fetch_and_parse raises on a non-2xx response."""

        def fake_get(url, timeout=None, follow_redirects=None):
            return httpx.Response(
                status_code=404,
                text="Not found",
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        with pytest.raises(httpx.HTTPStatusError):
            parser.fetch_and_parse("https://gone.dev")

    def test_fetch_and_parse_non_html_content_type(self, parser, monkeypatch):
        """Test fetch_and_parse raises ValueError for non-HTML content (e.g. a PDF)."""

        def fake_get(url, timeout=None, follow_redirects=None):
            return httpx.Response(
                status_code=200,
                headers={"content-type": "application/pdf"},
                content=b"%PDF-1.4",
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        with pytest.raises(ValueError):
            parser.fetch_and_parse("https://resume.pdf")
