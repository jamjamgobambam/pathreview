"""Tests for resume_parser.py"""

from unittest.mock import Mock, patch

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.resume_parser import ResumeParser


@pytest.mark.unit
class TestResumeParser:
    """Test suite for ResumeParser."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance."""
        return ResumeParser()

    def test_parse_single_column_resume_text(self, parser, sample_resume_text):
        """Test parsing a standard single-column resume text."""
        result = parser.parse(sample_resume_text)

        assert isinstance(result, ParseResult)
        assert result.text
        assert result.source_type == "resume"
        assert result.metadata["source_type"] == "resume"
        assert result.metadata["page_count"] == 1
        assert "detected_sections" in result.metadata
        # Should detect common sections like Experience, Skills, Education
        detected_lower = [s.lower() for s in result.metadata["detected_sections"]]
        assert any("experience" in s for s in detected_lower) or any(
            "skills" in s for s in detected_lower
        )

    def test_parse_resume_no_work_experience(self, parser):
        """Test parsing a resume with no work experience section - handles gracefully."""
        resume_no_work = """
        John Smith
        Software Developer
        john@example.com

        Education:
        - B.S. Computer Science, University (2023)

        Skills: Python, JavaScript, React
        """
        result = parser.parse(resume_no_work)

        assert isinstance(result, ParseResult)
        assert result.text
        # Should not crash even with missing Experience section
        assert result.metadata["page_count"] == 1
        detected_lower = [s.lower() for s in result.metadata["detected_sections"]]
        assert any("education" in s for s in detected_lower)

    def test_parse_multipage_pdf(self, parser):
        """Test parsing a multi-page PDF resume."""
        # Create a mock PDF with multiple pages
        with patch("ingestion.parsers.resume_parser.PdfReader") as mock_pdf_reader:
            # Setup mock PDF with 3 pages
            mock_page1 = Mock()
            mock_page1.extract_text.return_value = "Page 1 Content\nJohn Doe\nExperience:"

            mock_page2 = Mock()
            mock_page2.extract_text.return_value = "Page 2 Content\nSenior Developer at TechCorp"

            mock_page3 = Mock()
            mock_page3.extract_text.return_value = "Page 3 Content\nEducation: BS CS"

            mock_reader = Mock()
            mock_reader.pages = [mock_page1, mock_page2, mock_page3]
            mock_pdf_reader.return_value = mock_reader

            pdf_bytes = b"fake pdf content"
            result = parser.parse(pdf_bytes)

            assert isinstance(result, ParseResult)
            assert result.metadata["page_count"] == 3
            assert "Page 1 Content" in result.text
            assert "Page 2 Content" in result.text
            assert "Page 3 Content" in result.text

    def test_parse_markdown_resume(self, parser):
        """Test parsing a Markdown resume."""
        markdown_resume = """
        # Jane Doe
        ## Contact
        - Email: jane@example.com
        - GitHub: github.com/janedoe

        ## Experience
        - **Software Engineer** at TechCorp (2022-2024)
          - Built REST APIs using Python and FastAPI

        ## Skills
        - Python, JavaScript, React, PostgreSQL
        """
        result = parser.parse(markdown_resume)

        assert isinstance(result, ParseResult)
        assert result.source_type == "resume"
        assert result.metadata["page_count"] == 1
        # Markdown syntax should be stripped
        assert "#" not in result.text or result.text.count("#") < markdown_resume.count("#")
        assert "Jane Doe" in result.text

    def test_parse_invalid_content_type(self, parser):
        """Test that invalid content type raises ValueError with clear message."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)  # Invalid: integer

        assert "Content must be bytes" in str(exc_info.value) or "Content must be" in str(
            exc_info.value
        )

    def test_parse_invalid_list_content(self, parser):
        """Test that list content raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(["not", "valid"])

        assert "Content must be bytes" in str(exc_info.value) or "Content must be" in str(
            exc_info.value
        )

    def test_detect_sections(self, parser):
        """Test section detection in resume text."""
        text = """
        Experience:
        Senior Developer at TechCorp

        Education:
        BS Computer Science

        Skills: Python, JavaScript
        """
        sections = parser._detect_sections(text)

        assert isinstance(sections, list)
        assert len(sections) > 0
        sections_lower = [s.lower() for s in sections]
        assert any("experience" in s for s in sections_lower)
        assert any("education" in s for s in sections_lower)
        assert any("skills" in s for s in sections_lower)

    # Edge Case: Indented headers with leading whitespace should still be detected
    def test_detect_sections_indented_headers(self, parser):
        """Mixed indentation (spaces and tabs) — headers still detected."""
        text = "\tExperience:\n    Education:\n        Skills: Python"
        sections = [s.lower() for s in parser._detect_sections(text)]
        assert "experience" in sections
        assert "education" in sections
        assert "skills" in sections

    # Edge Case: Non-indented headers should still be detected
    def test_detect_sections_non_indented_headers(self, parser):
        """Flush-left headers keep working (no regression)."""
        text = "Experience:\nEducation:\nSkills: Python"
        sections = [s.lower() for s in parser._detect_sections(text)]
        assert "experience" in sections
        assert "education" in sections
        assert "skills" in sections

    # Edge Case: Section words inside sentences should not be detected
    def test_detect_sections_ignores_midsentence_words(self, parser):
        """A section word inside a sentence is not a header."""
        text = "I gained a lot of experience and skills at my last job."
        sections = [s.lower() for s in parser._detect_sections(text)]
        assert "experience" not in sections
        assert "skills" not in sections

    # Edge Case: Section words as substrings of other words should not be detected
    def test_detect_sections_ignores_substring_words(self, parser):
        """Words that merely contain a header as a substring are not detected."""
        text = "Experienced Engineer\nSkillset overview"
        sections = [s.lower() for s in parser._detect_sections(text)]
        assert "experience" not in sections
        assert "skills" not in sections

    # Edge Case: Headers on the very first line should still be detected
    def test_detect_sections_first_line_header(self, parser):
        """A header on the very first line (no preceding newline) is detected."""
        text = "Skills: Python\nMore content here"
        sections = [s.lower() for s in parser._detect_sections(text)]
        assert "skills" in sections

    # Edge Case: Headers with trailing whitespace should still be detected
    def test_detect_sections_trailing_whitespace(self, parser):
        """A header with trailing whitespace is still detected."""
        text = "Education   \n- B.S. Computer Science"
        sections = [s.lower() for s in parser._detect_sections(text)]
        assert "education" in sections

    # Edge Case: Repeated headers should be detected only once
    def test_detect_sections_deduplicates(self, parser):
        """A repeated header is reported only once."""
        text = "Skills: Python\nSkills: JavaScript"
        sections = parser._detect_sections(text)
        assert sections.count("Skills") == 1

    def test_strip_markdown_syntax(self, parser):
        """Test markdown syntax stripping."""
        markdown_text = """
        # Header
        **Bold text** and _italic text_
        [Link](https://example.com)
        ```python
        print("code")
        ```
        `inline code`
        """
        stripped = parser._strip_markdown(markdown_text)

        # Headers should be removed
        assert not stripped.strip().startswith("#")
        # Code blocks should be removed
        assert "print" not in stripped or "```" not in stripped
        # But actual text content should remain
        assert "Header" in stripped or "Bold text" in stripped

    def test_pdf_parsing_error_handling(self, parser):
        """Test graceful error handling for invalid PDF."""
        with patch("ingestion.parsers.resume_parser.PdfReader") as mock_pdf_reader:
            mock_pdf_reader.side_effect = Exception("Invalid PDF format")

            with pytest.raises(ValueError) as exc_info:
                parser.parse(b"invalid pdf bytes")

            assert "Failed to parse PDF" in str(exc_info.value)

    def test_parse_preserves_text_content(self, parser):
        """Test that parsing preserves actual content text."""
        original_text = "John Doe\nSoftware Engineer\nPython, JavaScript, React"
        result = parser.parse(original_text)

        assert "John Doe" in result.text
        assert "Software Engineer" in result.text
        assert "Python" in result.text
