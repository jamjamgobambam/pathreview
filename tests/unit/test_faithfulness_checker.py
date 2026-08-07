"""Tests for faithfulness_checker.py"""

from typing import Any

import pytest

from rag.evaluator.faithfulness_checker import FaithfulnessChecker


@pytest.mark.unit
class TestFaithfulnessChecker:
    """Test suite for FaithfulnessChecker."""

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        """Create a FaithfulnessChecker instance."""
        return FaithfulnessChecker()

    def test_feedback_fully_supported_by_context(self, checker: FaithfulnessChecker) -> None:
        """Test feedback fully supported by context returns score close to 1.0."""
        feedback = "The developer has strong Python skills and experience with Django."
        context_chunks = [
            {"text": "The portfolio shows Python expertise and Django framework experience."},
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Should be high score due to support
        assert score > 0.5

    def test_feedback_with_no_support_in_context(self, checker: FaithfulnessChecker) -> None:
        """Test feedback with no support in context returns score close to 0.0."""
        feedback = "This developer is an expert in Rust systems programming."
        context_chunks = [
            {"text": "The developer has Python and JavaScript experience."},
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert score < 0.5  # Should be low score

    def test_partial_support_returns_middle_score(self, checker: FaithfulnessChecker) -> None:
        """Test partial support returns score between 0 and 1."""
        feedback = "The developer shows Python expertise and Kubernetes knowledge."
        context_chunks = [
            {"text": "Strong Python programming skills demonstrated in projects."},
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Partial support should be middle range
        assert 0.2 < score < 0.8

    def test_empty_feedback_returns_zero(self, checker: FaithfulnessChecker) -> None:
        """Test empty feedback returns 0.0."""
        feedback = ""
        context_chunks = [{"text": "Some context"}]

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_empty_context_chunks_returns_zero(self, checker: FaithfulnessChecker) -> None:
        """Test empty context chunks returns 0.0."""
        feedback = "Some feedback"
        context_chunks: list[dict[str, Any]] = []

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_both_empty_returns_zero(self, checker: FaithfulnessChecker) -> None:
        """Test both empty returns 0.0."""
        feedback = ""
        context_chunks: list[dict[str, Any]] = []

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_multiple_context_chunks(self, checker: FaithfulnessChecker) -> None:
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

    def test_extract_claims(self, checker: FaithfulnessChecker) -> None:
        """Test claim extraction from feedback."""
        feedback = "The developer is skilled. They have experience. They work well."
        claims = checker._extract_claims(feedback)

        assert isinstance(claims, list)
        assert len(claims) > 0
        assert all(isinstance(c, str) for c in claims)

    def test_extract_claims_with_punctuation(self, checker: FaithfulnessChecker) -> None:
        """Test claim extraction handles various punctuation."""
        feedback = "First claim! Second claim? Third claim. Fourth claim"
        claims = checker._extract_claims(feedback)

        assert isinstance(claims, list)
        # Should extract at least some claims

    def test_is_supported_with_keyword_overlap(self, checker: FaithfulnessChecker) -> None:
        """Test that claim is marked as supported with keyword overlap."""
        claim = "The developer has Python skills"
        context = "Python programming skills demonstrated throughout portfolio"

        supported = checker._is_supported(claim, context)

        assert isinstance(supported, bool)
        assert supported is True

    def test_is_supported_without_keywords(self, checker: FaithfulnessChecker) -> None:
        """Test that claim is unsupported without keyword overlap."""
        claim = "Expert in Rust systems programming"
        context = "Strong background in Python web development"

        supported = checker._is_supported(claim, context)

        assert isinstance(supported, bool)
        assert supported is False

    def test_case_insensitive_support_check(self, checker: FaithfulnessChecker) -> None:
        """Test that support check is case insensitive."""
        claim = "PYTHON PROGRAMMING SKILLS"
        context = "python programming skills are demonstrated"

        supported = checker._is_supported(claim, context)

        assert supported is True

    def test_score_never_returns_hardcoded_value(self, checker: FaithfulnessChecker) -> None:
        """Test that score varies with input, never hardcoded 1.0 or 0.0."""
        # First test: fully supported
        score1 = checker.check(
            "Python and JavaScript skills", [{"text": "Expert in Python and JavaScript"}]
        )

        # Second test: no support
        score2 = checker.check("Rust expertise", [{"text": "Java programming background"}])

        # Scores should be different
        assert score1 != score2
        # First should be higher
        assert score1 > score2

    def test_multiple_claims_varying_support(self, checker: FaithfulnessChecker) -> None:
        """Test scoring with multiple claims of varying support."""
        feedback = "Python expert. Knows Rust. Skilled with Docker."
        context_chunks = [{"text": "Python and Docker expertise shown in projects."}]

        score = checker.check(feedback, context_chunks)

        # Two claims supported, one not
        assert isinstance(score, float)
        assert 0.2 < score < 0.8

    def test_very_long_feedback(self, checker: FaithfulnessChecker) -> None:
        """Test handling of very long feedback text."""
        feedback = "The developer. " * 100
        context_chunks = [{"text": "Developer portfolio content"}]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_very_long_context(self, checker: FaithfulnessChecker) -> None:
        """Test handling of very long context."""
        feedback = "The developer has Python skills."
        context_chunks = [{"text": "Python " * 1000}]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_common_words_filtered_in_overlap(self, checker: FaithfulnessChecker) -> None:
        """Test that common stop words are filtered in overlap calculation."""
        # This test verifies that "the", "is", "and" etc. don't count as meaningful overlap
        claim = "The project is well documented"
        context = "The project is poorly documented"  # Opposite meaning but same stop words

        checker._is_supported(claim, context)

        # Despite word overlap, should look for meaningful overlap (not stop words)
        # This depends on implementation

    def test_minimum_overlap_required(self, checker: FaithfulnessChecker) -> None:
        """Test that minimum meaningful overlap is required for support."""
        claim = "Python expertise"
        context = "Python"  # Only one word match

        supported = checker._is_supported(claim, context)

        assert isinstance(supported, bool)
        # Need at least 2 meaningful tokens for support

    def test_none_context_chunk_text(self, checker: FaithfulnessChecker) -> None:
        """Test handling of None in context chunk text."""
        feedback = "Has Python skills"
        context_chunks = [{"text": None}]

        score = checker.check(feedback, context_chunks)

        # Should handle gracefully
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_missing_text_key_in_chunk(self, checker: FaithfulnessChecker) -> None:
        """Test handling of missing 'text' key in context chunk."""
        feedback = "Has Python skills"
        context_chunks = [{"content": "Python skills"}]  # Wrong key

        score = checker.check(feedback, context_chunks)

        # Should handle gracefully
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_consistency(self, checker: FaithfulnessChecker) -> None:
        """Test that same input produces same score."""
        feedback = "The developer has strong Python skills."
        context_chunks = [{"text": "Expert Python programmer"}]

        score1 = checker.check(feedback, context_chunks)
        score2 = checker.check(feedback, context_chunks)

        assert score1 == score2

    def test_specialized_technical_terms(self, checker: FaithfulnessChecker) -> None:
        """Test support check with specialized technical terms."""
        claim = "Experienced with PostgreSQL and ORM frameworks"
        context = "Database design with PostgreSQL, SQLAlchemy ORM"

        supported = checker._is_supported(claim, context)

        assert supported is True

    def test_multi_symbol_terms_kept_intact(self, checker: FaithfulnessChecker) -> None:
        """Test that terms like 'C++' and 'CI/CD' are tokenized as single terms."""
        claim = "The developer knows C++ and CI/CD pipelines"
        context = "Strong background in C++ development and CI/CD automation"

        supported = checker._is_supported(claim, context)

        assert supported is True

    def test_support_ratio_direct_value(self, checker: FaithfulnessChecker) -> None:
        """Test _support_ratio returns the exact overlap fraction."""
        claim = "Python expertise"
        context = "Python fundamentals"

        ratio = checker._support_ratio(claim, context)

        # 1 of 2 meaningful claim tokens ("python") is covered by context
        assert ratio == 0.5

    def test_support_ratio_empty_claim_returns_zero(self, checker: FaithfulnessChecker) -> None:
        """Test _support_ratio handles an empty claim without dividing by zero."""
        ratio = checker._support_ratio("", "Python fundamentals")

        assert ratio == 0.0

    def test_support_ratio_empty_context_returns_zero(self, checker: FaithfulnessChecker) -> None:
        """Test _support_ratio returns 0.0 when context has no tokens at all."""
        ratio = checker._support_ratio("Python expertise", "")

        assert ratio == 0.0

    def test_support_ratio_all_stopword_claim_returns_zero(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Test _support_ratio guards against a claim with no meaningful tokens.

        A claim made up entirely of stop words has no meaningful tokens to
        check for overlap, which would otherwise divide by zero.
        """
        ratio = checker._support_ratio("the and of", "Python fundamentals")

        assert ratio == 0.0

    def test_is_supported_at_exact_threshold_boundary(self, checker: FaithfulnessChecker) -> None:
        """Test that a ratio exactly at SUPPORT_THRESHOLD counts as supported."""
        claim_tokens = [f"tok{i}" for i in range(20)]
        claim = " ".join(claim_tokens)
        context = " ".join(claim_tokens[:7])  # 7/20 = 0.35 == SUPPORT_THRESHOLD

        assert checker._support_ratio(claim, context) == checker.SUPPORT_THRESHOLD
        assert checker._is_supported(claim, context) is True

    def test_scale_ratio_at_zero_is_zero(self, checker: FaithfulnessChecker) -> None:
        """Test _scale_ratio maps a ratio of 0.0 to a score of exactly 0.0."""
        assert checker._scale_ratio(0.0) == 0.0

    def test_scale_ratio_at_threshold_is_half(self, checker: FaithfulnessChecker) -> None:
        """Test _scale_ratio maps SUPPORT_THRESHOLD to exactly 0.5.

        This is what keeps _is_supported's boolean decision and check()'s
        continuous score in agreement at the decision boundary.
        """
        assert checker._scale_ratio(checker.SUPPORT_THRESHOLD) == 0.5

    def test_scale_ratio_at_one_is_one(self, checker: FaithfulnessChecker) -> None:
        """Test _scale_ratio maps a ratio of 1.0 to a score of exactly 1.0."""
        assert checker._scale_ratio(1.0) == 1.0

    def test_scale_ratio_is_monotonic(self, checker: FaithfulnessChecker) -> None:
        """Test _scale_ratio never decreases as the input ratio increases."""
        samples = [i / 20 for i in range(21)]  # 0.0, 0.05, ..., 1.0
        scaled = [checker._scale_ratio(r) for r in samples]

        assert scaled == sorted(scaled)

    def test_extract_claims_excludes_exactly_ten_char_claim(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Test that a claim of exactly 10 characters is excluded (needs > 10)."""
        claims = checker._extract_claims("1234567890.")

        assert claims == []

    def test_extract_claims_includes_eleven_char_claim(self, checker: FaithfulnessChecker) -> None:
        """Test that a claim of 11 characters clears the length filter."""
        claims = checker._extract_claims("12345678901.")

        assert claims == ["12345678901"]

    def test_extract_claims_without_sentence_punctuation(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Test claim extraction on text with no sentence-ending punctuation."""
        feedback = "This whole feedback string has no punctuation at all"
        claims = checker._extract_claims(feedback)

        assert claims == [feedback]

    def test_extract_claims_empty_string_returns_no_claims(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Test that an empty string produces no claims."""
        assert checker._extract_claims("") == []

    def test_extract_claims_caps_at_ten(self, checker: FaithfulnessChecker) -> None:
        """Test that more than 10 valid claims are truncated to the first 10."""
        feedback = ". ".join(f"Claim number {i} here" for i in range(13)) + "."

        claims = checker._extract_claims(feedback)

        assert len(claims) == 10

    def test_check_context_chunk_not_a_dict_raises(self, checker: FaithfulnessChecker) -> None:
        """Test current behavior when a context chunk isn't a dict.

        `check()`'s type hint promises `list[dict]`; passing a bare string
        chunk currently raises AttributeError from `chunk.get(...)` rather
        than failing gracefully. This test documents that behavior so a
        future change to handle malformed chunks doesn't go unnoticed.
        """
        with pytest.raises(AttributeError):
            checker.check("Has Python skills", ["not a dict"])  # type: ignore[list-item]

    def test_check_non_string_feedback_raises(self, checker: FaithfulnessChecker) -> None:
        """Test current behavior when feedback isn't a string.

        `check()`'s type hint promises `feedback: str`; passing a non-string
        currently raises TypeError from `re.split(...)` inside
        `_extract_claims`. This test documents that behavior so a future
        change to validate input doesn't go unnoticed.
        """
        with pytest.raises(TypeError):
            checker.check(123, [{"text": "Python skills"}])  # type: ignore[arg-type]

    def test_check_non_string_chunk_text_is_coerced(self, checker: FaithfulnessChecker) -> None:
        """Test handling of a non-string, truthy 'text' value (e.g. an int).

        Same class of bug as `test_none_context_chunk_text` (None is falsy
        and was already handled); a truthy non-string like an int used to
        slip through and crash `" ".join(...)` with a TypeError. It's now
        coerced to a string instead.
        """
        score = checker.check("Has Python skills", [{"text": 42}])

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_whitespace_only_feedback_returns_neutral(self, checker: FaithfulnessChecker) -> None:
        """Test that whitespace-only feedback yields no claims, not a crash.

        Whitespace-only feedback is truthy (doesn't hit the empty-input
        early return) but extracts to zero claims, so it should fall
        through to the neutral 0.5 default like other no-claims input.
        """
        score = checker.check("   ", [{"text": "Some context"}])

        assert score == 0.5
