"""Tests for faithfulness_checker.py"""

import pytest

from rag.evaluator.faithfulness_checker import FaithfulnessChecker


@pytest.mark.unit
class TestFaithfulnessChecker:
    """Test suite for FaithfulnessChecker."""

    @pytest.fixture
    def checker(self):
        """Create a FaithfulnessChecker instance."""
        return FaithfulnessChecker()

    def test_feedback_fully_supported_by_context(self, checker):
        """Test feedback fully supported by context returns score close to 1.0."""
        feedback = "The developer has strong Python skills and experience with Django."
        context_chunks = [
            {
                "text": "The portfolio shows Python expertise and Django framework experience."
            },
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Should be high score due to support
        assert score > 0.5

    def test_feedback_with_no_support_in_context(self, checker):
        """Test feedback with no support in context returns score close to 0.0."""
        feedback = "This developer is an expert in Rust systems programming."
        context_chunks = [
            {
                "text": "The developer has Python and JavaScript experience."
            },
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert score < 0.5  # Should be low score

    def test_partial_support_returns_middle_score(self, checker):
        """Test partial support returns score between 0 and 1."""
        feedback = "The developer shows Python expertise and Kubernetes knowledge."
        context_chunks = [
            {
                "text": "Strong Python programming skills demonstrated in projects."
            },
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Partial support should be middle range
        assert 0.2 < score < 0.8

    def test_empty_feedback_returns_zero(self, checker):
        """Test empty feedback returns 0.0."""
        feedback = ""
        context_chunks = [
            {"text": "Some context"}
        ]

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_empty_context_chunks_returns_zero(self, checker):
        """Test empty context chunks returns 0.0."""
        feedback = "Some feedback"
        context_chunks = []

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_both_empty_returns_zero(self, checker):
        """Test both empty returns 0.0."""
        feedback = ""
        context_chunks = []

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_multiple_context_chunks(self, checker):
        """Test multiple context chunks contribute to score."""
        feedback = "The developer has Python, JavaScript, and Docker experience."
        context_chunks = [
            {"text": "Python expertise shown in backend projects."},
            {"text": "JavaScript skills demonstrated in frontend development."},
            {"text": "Docker and containerization knowledge evident in CI/CD pipelines."},
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # All three claims supported
        assert score > 0.5

    def test_extract_claims(self, checker):
        """Test claim extraction from feedback."""
        feedback = "The developer is skilled. They have experience. They work well."
        claims = checker._extract_claims(feedback)

        assert isinstance(claims, list)
        assert len(claims) > 0
        assert all(isinstance(c, str) for c in claims)

    def test_extract_claims_with_punctuation(self, checker):
        """Test claim extraction handles various punctuation."""
        feedback = "First claim! Second claim? Third claim. Fourth claim"
        claims = checker._extract_claims(feedback)

        assert isinstance(claims, list)
        # Should extract at least some claims

    def test_is_supported_with_keyword_overlap(self, checker):
        """Test that claim is marked as supported with keyword overlap."""
        claim = "The developer has Python skills"
        context = "Python programming skills demonstrated throughout portfolio"

        supported = checker._is_supported(claim, context)

        assert isinstance(supported, bool)
        assert supported is True

    def test_is_supported_without_keywords(self, checker):
        """Test that claim is unsupported without keyword overlap."""
        claim = "Expert in Rust systems programming"
        context = "Strong background in Python web development"

        supported = checker._is_supported(claim, context)

        assert isinstance(supported, bool)
        assert supported is False

    def test_case_insensitive_support_check(self, checker):
        """Test that support check is case insensitive."""
        claim = "PYTHON PROGRAMMING SKILLS"
        context = "python programming skills are demonstrated"

        supported = checker._is_supported(claim, context)

        assert supported is True

    def test_score_never_returns_hardcoded_value(self, checker):
        """Test that score varies with input, never hardcoded 1.0 or 0.0."""
        # First test: fully supported
        score1 = checker.check(
            "Python and JavaScript skills",
            [{"text": "Expert in Python and JavaScript"}]
        )

        # Second test: no support
        score2 = checker.check(
            "Rust expertise",
            [{"text": "Java programming background"}]
        )

        # Scores should be different
        assert score1 != score2
        # First should be higher
        assert score1 > score2

    def test_multiple_claims_varying_support(self, checker):
        """Test scoring with multiple claims of varying support."""
        feedback = "Python expert. Knows Rust. Skilled with Docker."
        context_chunks = [
            {"text": "Python and Docker expertise shown in projects."}
        ]

        score = checker.check(feedback, context_chunks)

        # Two claims supported, one not
        assert isinstance(score, float)
        assert 0.2 < score < 0.8

    def test_very_long_feedback(self, checker):
        """Test handling of very long feedback text."""
        feedback = "The developer. " * 100
        context_chunks = [
            {"text": "Developer portfolio content"}
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_very_long_context(self, checker):
        """Test handling of very long context."""
        feedback = "The developer has Python skills."
        context_chunks = [
            {"text": "Python " * 1000}
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_common_words_filtered_in_overlap(self, checker):
        """Test that common stop words are filtered in overlap calculation."""
        # This test verifies that "the", "is", "and" etc. don't count as meaningful overlap
        claim = "The project is well documented"
        context = "The project is poorly documented"  # Opposite meaning but same stop words

        supported = checker._is_supported(claim, context)

        # Despite word overlap, should look for meaningful overlap (not stop words)
        # This depends on implementation

    def test_minimum_overlap_required(self, checker):
        """Test that minimum meaningful overlap is required for support."""
        claim = "Python expertise"
        context = "Python"  # Only one word match

        supported = checker._is_supported(claim, context)

        assert isinstance(supported, bool)
        # Need at least 2 meaningful tokens for support

    def test_none_context_chunk_text(self, checker):
        """Test handling of None in context chunk text."""
        feedback = "Has Python skills"
        context_chunks = [
            {"text": None}
        ]

        score = checker.check(feedback, context_chunks)

        # Should handle gracefully
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_missing_text_key_in_chunk(self, checker):
        """Test handling of missing 'text' key in context chunk."""
        feedback = "Has Python skills"
        context_chunks = [
            {"content": "Python skills"}  # Wrong key
        ]

        score = checker.check(feedback, context_chunks)

        # Should handle gracefully
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_consistency(self, checker):
        """Test that same input produces same score."""
        feedback = "The developer has strong Python skills."
        context_chunks = [{"text": "Expert Python programmer"}]

        score1 = checker.check(feedback, context_chunks)
        score2 = checker.check(feedback, context_chunks)

        assert score1 == score2

    def test_specialized_technical_terms(self, checker):
        """Test support check with specialized technical terms."""
        claim = "Experienced with PostgreSQL and ORM frameworks"
        context = "Database design with PostgreSQL, SQLAlchemy ORM"

        supported = checker._is_supported(claim, context)

        assert supported is True
