"""Tests for web_parser.py"""

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

    def test_parse_html_portfolio_page(self, parser):
        """Parses a portfolio HTML page into readable text and metadata."""
        html = """
        <html>
          <head>
            <title>Jane Doe | Portfolio</title>
            <meta name="description" content="Software engineer building AI products." />
          </head>
          <body>
            <h1>Jane Doe</h1>
            <p>I'm a software engineer focused on AI and backend systems.</p>
            <h2>Featured Projects</h2>
            <p>PathReview is an AI portfolio review assistant.</p>
            <a href="https://example.com/project">Project link</a>
          </body>
        </html>
        """

        result = parser.parse(html)

        assert isinstance(result, ParseResult)
        assert result.source_type == "web"
        assert "Jane Doe" in result.text
        assert "software engineer focused on ai and backend systems" in result.text.lower()
        assert "pathreview" in result.text.lower()
        assert result.metadata["source_type"] == "web"
        assert result.metadata["title"] == "Jane Doe | Portfolio"
        assert result.metadata["word_count"] > 0

    def test_parse_empty_html_returns_empty_text(self, parser):
        """Empty HTML should not crash and should produce an empty result set."""
        result = parser.parse("<html><body></body></html>")

        assert isinstance(result, ParseResult)
        assert result.source_type == "web"
        assert result.text == ""
        assert result.metadata["word_count"] == 0
        assert result.metadata["title"] == ""
