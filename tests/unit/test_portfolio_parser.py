"""Tests for portfolio_parser.py"""

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.portfolio_parser import PortfolioParser


@pytest.mark.unit
class TestPortfolioParser:
    """Test suite for PortfolioParser."""

    @pytest.fixture
    def parser(self) -> PortfolioParser:
        """Create a PortfolioParser instance."""
        return PortfolioParser()

    def test_parse_portfolio_page(
        self,
        parser: PortfolioParser,
        monkeypatch,
    ) -> None:
        """Test extracting text from a portfolio webpage."""

        class MockResponse:
            text = """
            <html>
                <body>
                    <h1>John Doe Portfolio</h1>
                    <p>Machine Learning Engineer</p>
                </body>
            </html>
            """

            def raise_for_status(self) -> None:
                pass

        monkeypatch.setattr(
            "ingestion.parsers.portfolio_parser.requests.get",
            lambda *args, **kwargs: MockResponse(),
        )

        result = parser.parse("https://example.com")

        assert isinstance(result, ParseResult)
        assert result.source_type == "portfolio"
        assert "John Doe Portfolio" in result.text
        assert "Machine Learning Engineer" in result.text
        assert result.metadata["source_type"] == "portfolio"
        assert result.metadata["url"] == "https://example.com"
        assert result.metadata["character_count"] > 0

    def test_invalid_content_type(
        self,
        parser: PortfolioParser,
    ) -> None:
        """Test invalid input type raises ValueError."""

        with pytest.raises(ValueError):
            parser.parse(12345)
