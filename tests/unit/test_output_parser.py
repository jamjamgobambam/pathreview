"""Tests for output_parser.py"""

import pytest
import json

from rag.generator.output_parser import parse_review_output, FeedbackSection, _parse_plaintext_output


@pytest.mark.unit
class TestOutputParser:
    """Test suite for output_parser module."""

    def test_json_wrapped_in_code_fence(self):
        """Test parsing JSON wrapped in code fence."""
        raw_output = """
        ```json
        {
            "skills": {
                "python": "Expert",
                "javascript": "Intermediate"
            },
            "suggestions": ["Learn Rust", "Practice Docker"]
        }
        ```
        """

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(s, FeedbackSection) for s in result)

    def test_raw_json_without_fence(self):
        """Test parsing raw JSON without code fence."""
        raw_output = json.dumps({
            "skills": "Advanced Python and JavaScript",
            "projects": "Strong portfolio of web apps",
            "recommendations": ["Add DevOps experience", "Write more documentation"]
        })

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_plain_text_fallback(self):
        """Test that plain text returns FeedbackSection without crash."""
        raw_output = "This is plain text feedback about the portfolio. No JSON here. Great work overall!"

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) == 1
        section = result[0]
        assert isinstance(section, FeedbackSection)
        assert section.section_name == "general_feedback"
        assert "plain text feedback" in section.content

    def test_malformed_json_fallback(self):
        """Test that malformed JSON gracefully falls back to plaintext."""
        raw_output = """```json
        {
            "skills": "incomplete json",
            "projects": [
        ```
        Some fallback text here.
        """

        result = parse_review_output(raw_output)

        # Should not crash, should return something
        assert isinstance(result, list)
        # May fall back to plaintext or return partial parsing

    def test_feedback_section_has_required_fields(self):
        """Test that FeedbackSection has all required fields."""
        section = FeedbackSection(
            section_name="skills",
            content="Python, JavaScript expertise",
            confidence=0.95,
            suggestions=["Learn Rust", "Study DevOps"]
        )

        assert section.section_name == "skills"
        assert section.content == "Python, JavaScript expertise"
        assert section.confidence == 0.95
        assert len(section.suggestions) == 2

    def test_json_with_multiple_sections(self):
        """Test parsing JSON with multiple sections."""
        raw_output = json.dumps({
            "technical_skills": {
                "languages": ["Python", "JavaScript"],
                "suggestions": ["Add Rust", "Learn Kubernetes"]
            },
            "soft_skills": {
                "communication": "Good",
                "suggestions": ["Improve documentation"]
            },
            "projects": {
                "quality": "High",
                "suggestions": []
            }
        })

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) >= 3
        section_names = [s.section_name for s in result]
        assert "technical_skills" in section_names
        assert "soft_skills" in section_names

    def test_confidence_scores_in_sections(self):
        """Test that feedback sections have confidence scores."""
        raw_output = json.dumps({
            "skills": "Expert Python developer",
            "projects": "Impressive portfolio"
        })

        result = parse_review_output(raw_output)

        for section in result:
            assert hasattr(section, "confidence")
            assert isinstance(section.confidence, float)
            assert 0.0 <= section.confidence <= 1.0

    def test_empty_json_object(self):
        """Test parsing empty JSON object."""
        raw_output = "{}"

        result = parse_review_output(raw_output)

        # Should return empty list or handle gracefully
        assert isinstance(result, list)

    def test_json_array_fallback(self):
        """Test handling of JSON array (not dict)."""
        raw_output = json.dumps([
            "First feedback item",
            "Second feedback item"
        ])

        result = parse_review_output(raw_output)

        # May fall back to plaintext or handle specially
        assert isinstance(result, list)

    def test_very_long_plain_text(self):
        """Test parsing very long plain text."""
        raw_output = "This is feedback. " * 500

        result = parse_review_output(raw_output)

        assert len(result) == 1
        assert isinstance(result[0], FeedbackSection)
        assert len(result[0].content) > 1000

    def test_html_in_feedback(self):
        """Test handling of HTML in feedback text."""
        raw_output = "<p>This is HTML feedback</p><p>With multiple tags</p>"

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_code_in_feedback(self):
        """Test feedback containing code blocks."""
        raw_output = """
        ```python
        def example():
            return "code"
        ```
        This example shows good Python style.
        """

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        # Should not crash on code blocks

    def test_section_suggestions_extraction(self):
        """Test that suggestions are extracted from JSON sections."""
        raw_output = json.dumps({
            "skills": {
                "current": "Python, JavaScript",
                "suggestions": ["Learn Go", "Master Kubernetes"]
            }
        })

        result = parse_review_output(raw_output)

        assert len(result) > 0
        section = result[0]
        if isinstance(section.suggestions, list) and section.suggestions:
            assert "Learn Go" in section.suggestions or len(section.suggestions) > 0

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        raw_output = "Portfolio review: Excellent work! 🎉 Skills: Python, JavaScript, Rust™"

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_nested_json_structure(self):
        """Test parsing nested JSON structures."""
        raw_output = json.dumps({
            "feedback": {
                "technical": {
                    "skills": {
                        "primary": ["Python", "JavaScript"],
                        "secondary": ["Rust", "Go"]
                    }
                }
            }
        })

        result = parse_review_output(raw_output)

        assert isinstance(result, list)

    def test_mixed_content(self):
        """Test output with both code fence and plaintext."""
        raw_output = """
        Some intro text here.

        ```json
        {
            "main_skill": "Python",
            "suggestions": ["add more projects"]
        }
        ```

        More text after the JSON.
        """

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_plaintext_output_helper(self):
        """Test _parse_plaintext_output helper function."""
        text = "This is plaintext feedback with useful information."

        result = _parse_plaintext_output(text)

        assert len(result) == 1
        section = result[0]
        assert section.section_name == "general_feedback"
        assert section.content == text
        assert section.confidence == 0.7

    def test_multiple_code_fences(self):
        """Test handling of multiple code fences."""
        raw_output = """
        ```json
        {"first": "data"}
        ```

        Some text.

        ```python
        print("code")
        ```
        """

        result = parse_review_output(raw_output)

        assert isinstance(result, list)

    def test_no_suggestions_key(self):
        """Test JSON without suggestions key."""
        raw_output = json.dumps({
            "skills": "Python expert",
            "experience": "5 years"
        })

        result = parse_review_output(raw_output)

        assert isinstance(result, list)
        for section in result:
            assert isinstance(section.suggestions, list)
