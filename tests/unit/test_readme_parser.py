"""Tests for readme_parser.py"""

import pytest

from ingestion.parsers.readme_parser import ReadmeParser
from ingestion.parsers.base import ParseResult


@pytest.mark.unit
class TestReadmeParser:
    """Test suite for ReadmeParser."""

    @pytest.fixture
    def parser(self):
        """Create a ReadmeParser instance."""
        return ReadmeParser()

    def test_parse_standard_readme(self, parser, sample_readme_text):
        """Test parsing a standard README."""
        result = parser.parse(sample_readme_text)

        assert isinstance(result, ParseResult)
        assert result.text == sample_readme_text
        assert result.source_type == "readme"
        assert result.metadata["source_type"] == "readme"
        assert "heading_count" in result.metadata
        assert result.metadata["heading_count"] > 0
        assert "word_count" in result.metadata
        assert result.metadata["word_count"] > 0

    def test_parse_readme_longer_than_10000_chars(self, parser):
        """Test parsing a README longer than 10,000 characters - full text preserved."""
        # Create a README with > 10,000 characters
        large_readme = "# Large README\n"
        for i in range(300):
            large_readme += f"## Section {i}\n"
            large_readme += f"Content for section {i}. " * 10 + "\n"

        assert len(large_readme) > 10000

        result = parser.parse(large_readme)

        assert isinstance(result, ParseResult)
        # Full text should be preserved, no truncation
        assert result.text == large_readme
        assert len(result.text) == len(large_readme)
        assert result.metadata["word_count"] > 100

    def test_parse_readme_with_code_blocks(self, parser):
        """Test parsing README with code blocks."""
        readme_with_code = """
        # Project
        This is a sample project.

        ## Installation
        ```bash
        pip install package
        ```

        ## Usage
        ```python
        import package
        package.run()
        ```
        """
        result = parser.parse(readme_with_code)

        assert isinstance(result, ParseResult)
        assert result.metadata["has_code_blocks"] is True

    def test_parse_readme_without_code_blocks(self, parser):
        """Test parsing README without code blocks."""
        readme_no_code = """
        # Project
        This is a text-only README.

        ## Features
        - Feature 1
        - Feature 2

        ## Installation
        Just install it!
        """
        result = parser.parse(readme_no_code)

        assert isinstance(result, ParseResult)
        assert result.metadata["has_code_blocks"] is False

    def test_parse_empty_readme(self, parser):
        """Test parsing empty README - returns empty ParseResult without crashing."""
        result = parser.parse("")

        assert isinstance(result, ParseResult)
        assert result.text == ""
        assert result.metadata["word_count"] == 0
        assert result.metadata["heading_count"] == 0
        assert result.source_type == "readme"

    def test_parse_readme_with_only_whitespace(self, parser):
        """Test parsing README with only whitespace."""
        result = parser.parse("   \n\n  \t  ")

        assert isinstance(result, ParseResult)
        assert result.metadata["word_count"] == 0

    def test_parse_readme_bytes_input(self, parser):
        """Test parsing README from bytes input."""
        readme_bytes = b"# Test README\nContent here"
        result = parser.parse(readme_bytes)

        assert isinstance(result, ParseResult)
        assert "Test README" in result.text
        assert "Content here" in result.text

    def test_parse_readme_bytes_with_utf8(self, parser):
        """Test parsing README bytes with UTF-8 characters."""
        readme_bytes = "# Café README\nThis has émojis 🎉".encode("utf-8")
        result = parser.parse(readme_bytes)

        assert isinstance(result, ParseResult)
        assert "Café" in result.text or "Caf" in result.text

    def test_parse_invalid_content_type(self, parser):
        """Test that invalid content type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)

        assert "Content must be a string or bytes" in str(exc_info.value)

    def test_extract_heading_hierarchy(self, parser):
        """Test heading hierarchy extraction."""
        markdown = """
        # Main Title
        Some content

        ## Subsection
        More content

        ### Sub-subsection
        Even more content

        ## Another Section
        Final content
        """
        headings = parser._extract_heading_hierarchy(markdown)

        assert isinstance(headings, list)
        assert len(headings) > 0
        # Check that levels are captured
        levels = [h["level"] for h in headings]
        assert 1 in levels
        assert 2 in levels
        assert 3 in levels

    def test_extract_heading_hierarchy_no_headings(self, parser):
        """Test heading extraction from text with no headings."""
        text = "Just some plain text without any markdown headings."
        headings = parser._extract_heading_hierarchy(text)

        assert isinstance(headings, list)
        assert len(headings) == 0

    def test_parse_readme_with_badges(self, parser):
        """Test parsing README with badges."""
        readme_with_badges = """
        # Project
        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)

        Content here.
        """
        result = parser.parse(readme_with_badges)

        assert isinstance(result, ParseResult)
        assert result.metadata["has_badges"] is True

    def test_parse_readme_without_badges(self, parser):
        """Test parsing README without badges."""
        readme_no_badges = """
        # Project
        Just regular content without any badges.
        """
        result = parser.parse(readme_no_badges)

        assert isinstance(result, ParseResult)
        assert result.metadata["has_badges"] is False

    def test_metadata_structure(self, parser):
        """Test that metadata has required structure."""
        result = parser.parse("# Test\nContent")

        assert "source_type" in result.metadata
        assert "heading_count" in result.metadata
        assert "word_count" in result.metadata
        assert "has_code_blocks" in result.metadata
        assert "has_badges" in result.metadata
        assert result.metadata["source_type"] == "readme"

    def test_word_count_accuracy(self, parser):
        """Test word count accuracy."""
        text = "This is a test with exactly ten words in the readme text"
        result = parser.parse(text)

        # Should count individual words
        assert result.metadata["word_count"] >= 10
        assert isinstance(result.metadata["word_count"], int)
