"""Reproduction test for issue #11: portfolio URL ingestion is missing.

There is no ingestion path for a profile's portfolio_url today: no
ingestion/parsers/web_parser.py exists, and IngestionPipeline has no
ingest_portfolio method. These tests fail against the current codebase,
demonstrating the gap described in the issue.
"""

import pytest

from ingestion.parsers.base import ParseResult


@pytest.mark.unit
class TestWebParser:
    """Test suite for the not-yet-implemented WebParser."""

    def test_web_parser_module_exists(self):
        """A web_parser module should exist alongside the other parsers."""
        from ingestion.parsers.web_parser import WebParser  # noqa: F401

    def test_parse_portfolio_page_html(self):
        """Parsing a portfolio page's HTML should extract bio/project text."""
        from ingestion.parsers.web_parser import WebParser

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

        parser = WebParser()
        result = parser.parse(sample_html)

        assert isinstance(result, ParseResult)
        assert result.source_type == "web"
        assert "Jane Doe" in result.text
        assert "Weather App" in result.text


@pytest.mark.unit
class TestIngestionPipelinePortfolio:
    """The pipeline should be able to ingest a portfolio URL end-to-end."""

    def test_ingest_portfolio_method_exists(self):
        """IngestionPipeline should expose an ingest_portfolio method."""
        from ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline(vector_db=None, db_session=None, embedding_provider=None)

        assert hasattr(pipeline, "ingest_portfolio")
