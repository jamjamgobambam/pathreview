"""Regression tests for issue #147: indented resume section headers."""

from __future__ import annotations

import pytest

from ingestion.parsers.resume_parser import ResumeParser


@pytest.mark.unit
class TestResumeSectionWhitespace:
    """Section detection must tolerate leading whitespace (PDF-style extracts)."""

    @pytest.fixture
    def parser(self) -> ResumeParser:
        """Create a ResumeParser instance."""
        return ResumeParser()

    def test_issue_147_indented_education_and_skills(self, parser: ResumeParser) -> None:
        """Exact sample from https://github.com/ascherj/pathreview/issues/147."""
        text = (
            "\n    John Smith\n    john@example.com\n\n"
            "    Education:\n    - B.S. Computer Science\n\n"
            "    Skills: Python\n"
        )
        result = parser.parse(text)
        sections_lower = [s.lower() for s in result.metadata["detected_sections"]]

        assert "education" in sections_lower
        assert "skills" in sections_lower

    def test_detect_sections_flush_left_still_works(self, parser: ResumeParser) -> None:
        """Flush-left headers must keep working after the whitespace fix."""
        text = "Experience:\nAcme Corp\n\nEducation:\nBS CS\n\nSkills: Python\n"
        sections_lower = [s.lower() for s in parser._detect_sections(text)]

        assert "experience" in sections_lower
        assert "education" in sections_lower
        assert "skills" in sections_lower

    def test_detect_multiword_header_with_indent(self, parser: ResumeParser) -> None:
        """Indented multi-word headers like Work Experience are detected."""
        text = "\n    Work Experience:\n    Engineer at Acme\n"
        sections_lower = [s.lower() for s in parser._detect_sections(text)]

        assert any("experience" in s for s in sections_lower)

    def test_detect_bare_header_line_with_indent(self, parser: ResumeParser) -> None:
        """Indented header with no trailing colon still matches end-of-line pattern."""
        text = "\n    Education\n    BS Computer Science\n"
        sections_lower = [s.lower() for s in parser._detect_sections(text)]

        assert "education" in sections_lower

    def test_no_sections_returns_empty(self, parser: ResumeParser) -> None:
        """Text without recognizable headers returns an empty list."""
        sections = parser._detect_sections("Just a bio with no labeled sections.")
        assert sections == []
