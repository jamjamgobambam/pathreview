"""Tests for web_parser.py"""

import httpx
import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.web_parser import (
    WebParser,
    WebParserError,
    fetch_url,
)

SAMPLE_HTML = """
<html>
  <head><title>Jane Dev Portfolio</title></head>
  <body>
    <nav>Home About Projects Contact</nav>
    <header>Site banner</header>
    <h1>About Me</h1>
    <p>I am a software engineer who builds web apps.</p>
    <section id="projects">
      <h2>Projects</h2>
      <p>Weather App: a React forecasting tool.</p>
    </section>
    <script>console.log("tracking");</script>
    <style>.hidden { display: none; }</style>
    <footer>Copyright 2026</footer>
  </body>
</html>
"""


@pytest.mark.unit
class TestWebParser:
    """Test suite for WebParser."""

    @pytest.fixture
    def parser(self):
        """Create a WebParser instance."""
        return WebParser()

    def test_parse_returns_parse_result(self, parser):
        """Parsing HTML returns a ParseResult with portfolio source type."""
        result = parser.parse(SAMPLE_HTML)

        assert isinstance(result, ParseResult)
        assert result.source_type == "portfolio"
        assert result.metadata["source_type"] == "portfolio"

    def test_parse_extracts_content_text(self, parser):
        """Meaningful content text is extracted."""
        result = parser.parse(SAMPLE_HTML)

        assert "I am a software engineer" in result.text
        assert "Weather App" in result.text

    def test_parse_strips_boilerplate(self, parser):
        """Script, style, nav, and footer content is removed."""
        result = parser.parse(SAMPLE_HTML)

        assert "tracking" not in result.text
        assert "display: none" not in result.text
        assert "Copyright 2026" not in result.text
        assert "Site banner" not in result.text

    def test_parse_metadata_fields(self, parser):
        """Metadata contains title, counts, and detected sections."""
        result = parser.parse(SAMPLE_HTML)

        assert result.metadata["title"] == "Jane Dev Portfolio"
        assert result.metadata["word_count"] > 0
        assert "about" in result.metadata["extracted_sections"]
        assert "project" in result.metadata["extracted_sections"]

    def test_parse_accepts_bytes(self, parser):
        """Bytes input is decoded and parsed."""
        result = parser.parse(SAMPLE_HTML.encode("utf-8"))

        assert "software engineer" in result.text

    def test_parse_empty_content_raises(self, parser):
        """Empty content raises WebParserError."""
        with pytest.raises(WebParserError):
            parser.parse("   ")

    def test_parse_no_text_raises(self, parser):
        """HTML with no extractable text raises WebParserError."""
        with pytest.raises(WebParserError):
            parser.parse("<html><body><script>x=1</script></body></html>")

    def test_parse_invalid_type_raises(self, parser):
        """Non-string/bytes content raises WebParserError."""
        with pytest.raises(WebParserError):
            parser.parse(12345)


@pytest.mark.unit
class TestFetchUrl:
    """Test suite for fetch_url and its SSRF guard."""

    def test_rejects_non_http_scheme(self):
        """Non-http(s) schemes are rejected."""
        with pytest.raises(WebParserError, match="http or https"):
            fetch_url("ftp://example.com/resource")

    def test_rejects_missing_hostname(self):
        """A URL without a hostname is rejected."""
        with pytest.raises(WebParserError):
            fetch_url("http://")

    def test_blocks_localhost(self):
        """localhost resolves to loopback and is blocked."""
        with pytest.raises(WebParserError, match="internal or non-public"):
            fetch_url("http://localhost/admin")

    def test_blocks_loopback_ip(self):
        """Loopback IPs are blocked."""
        with pytest.raises(WebParserError, match="internal or non-public"):
            fetch_url("http://127.0.0.1/")

    def test_blocks_cloud_metadata_endpoint(self):
        """The link-local cloud metadata address is blocked."""
        with pytest.raises(WebParserError, match="internal or non-public"):
            fetch_url("http://169.254.169.254/latest/meta-data/")

    def test_blocks_private_ip(self):
        """Private-range IPs are blocked."""
        with pytest.raises(WebParserError, match="internal or non-public"):
            fetch_url("http://10.0.0.5/")

    def test_fetch_success(self, monkeypatch):
        """A public HTML response is returned as text."""
        monkeypatch.setattr(
            "ingestion.parsers.web_parser._is_blocked_address",
            lambda host: False,
        )

        def fake_get(url, **kwargs):
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text="<html><body>hi</body></html>",
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        html = fetch_url("https://example.com")
        assert "hi" in html

    def test_fetch_rejects_non_html(self, monkeypatch):
        """Non-HTML content types are rejected."""
        monkeypatch.setattr(
            "ingestion.parsers.web_parser._is_blocked_address",
            lambda host: False,
        )

        def fake_get(url, **kwargs):
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                text="{}",
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        with pytest.raises(WebParserError, match="Expected HTML"):
            fetch_url("https://example.com/api")

    def test_fetch_http_error_wrapped(self, monkeypatch):
        """HTTP errors are wrapped in WebParserError."""
        monkeypatch.setattr(
            "ingestion.parsers.web_parser._is_blocked_address",
            lambda host: False,
        )

        def fake_get(url, **kwargs):
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(httpx, "get", fake_get)

        with pytest.raises(WebParserError, match="Failed to fetch"):
            fetch_url("https://example.com")

    def test_redirect_to_internal_is_blocked(self, monkeypatch):
        """A redirect from a public URL to an internal address is rejected."""
        # Only the redirect target (link-local metadata IP) is blocked.
        monkeypatch.setattr(
            "ingestion.parsers.web_parser._is_blocked_address",
            lambda host: host == "169.254.169.254",
        )

        def fake_get(url, **kwargs):
            return httpx.Response(
                302,
                headers={"location": "http://169.254.169.254/latest/meta-data/"},
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        with pytest.raises(WebParserError, match="internal or non-public"):
            fetch_url("https://public-site.example.com")

    def test_redirect_to_public_is_followed(self, monkeypatch):
        """A redirect to another public URL is followed and its HTML returned."""
        monkeypatch.setattr(
            "ingestion.parsers.web_parser._is_blocked_address",
            lambda host: False,
        )

        calls = {"n": 0}

        def fake_get(url, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(
                    301,
                    headers={"location": "https://www.example.com/home"},
                    request=httpx.Request("GET", url),
                )
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html><body>final</body></html>",
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        html = fetch_url("https://example.com")
        assert "final" in html
        assert calls["n"] == 2

    def test_too_many_redirects(self, monkeypatch):
        """An endless redirect loop is stopped."""
        monkeypatch.setattr(
            "ingestion.parsers.web_parser._is_blocked_address",
            lambda host: False,
        )

        def fake_get(url, **kwargs):
            return httpx.Response(
                302,
                headers={"location": "https://example.com/next"},
                request=httpx.Request("GET", url),
            )

        monkeypatch.setattr(httpx, "get", fake_get)

        with pytest.raises(WebParserError, match="Too many redirects"):
            fetch_url("https://example.com")
