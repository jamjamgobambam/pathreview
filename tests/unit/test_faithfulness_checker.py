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
            {"text": "The portfolio shows Python expertise and Django framework experience."},
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
            {"text": "The developer has Python and JavaScript experience."},
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert score < 0.5  # Should be low score

    def test_partial_support_returns_middle_score(self, checker):
        """Test partial support returns score between 0 and 1."""
        feedback = "The developer shows Python expertise and Kubernetes knowledge."
        context_chunks = [
            {"text": "Strong Python programming skills demonstrated in projects."},
        ]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # One of four required terms matches.
        assert score == pytest.approx(0.25)

    def test_empty_feedback_returns_zero(self, checker):
        """Test empty feedback returns 0.0."""
        feedback = ""
        context_chunks = [{"text": "Some context"}]

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
        assert score == pytest.approx(1.0)

    def test_extract_claims(self, checker):
        """Test claim extraction from feedback."""
        feedback = "The developer is skilled. They have experience. They work well."
        claims = checker._extract_claims(feedback)

        assert claims == [
            "The developer is skilled",
            "They have experience",
            "They work well",
        ]

    def test_extract_claims_with_punctuation(self, checker):
        """Test claim extraction handles various punctuation."""
        feedback = "First claim! Second claim? Third claim. Fourth claim"
        claims = checker._extract_claims(feedback)

        assert claims == ["First claim", "Second claim", "Third claim", "Fourth claim"]

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
            "Python and JavaScript skills", [{"text": "Expert in Python and JavaScript"}]
        )

        # Second test: no support
        score2 = checker.check("Rust expertise", [{"text": "Java programming background"}])

        # Scores should be different
        assert score1 != score2
        # First should be higher
        assert score1 > score2

    def test_multiple_claims_varying_support(self, checker):
        """Test scoring with multiple claims of varying support."""
        feedback = "Python expert. Knows Rust. Skilled with Docker."
        context_chunks = [{"text": "Python and Docker expertise shown in projects."}]

        score = checker.check(feedback, context_chunks)

        # (1/2 + 0 + 1/3) / 3
        assert score == pytest.approx(5 / 18)

    def test_supported_short_claims_score_fully(self, checker):
        """Reproduce issue #152 for two supported one-fact claims."""
        score = checker.check(
            "Knows Python. Knows SQL.",
            [{"text": "python expert"}, {"text": "sql expert"}],
        )

        assert score == pytest.approx(1.0)

    def test_short_claim_requires_its_fact_in_context(self, checker):
        """Keep the short-claim path from accepting unrelated evidence."""
        score = checker.check("Knows Rust.", [{"text": "Python and SQL projects"}])

        assert score == 0.0
        assert checker.check("Knows Python.", [{"text": "non_python work"}]) == 0.0

    def test_mixed_short_claims_keep_per_claim_proportions(self, checker):
        """One grounded and one ungrounded short claim score one half."""
        score = checker.check(
            "Knows Python. Knows Rust.",
            [{"text": "Python projects"}],
        )

        assert score == pytest.approx(0.5)

    @pytest.mark.parametrize(
        "feedback",
        [
            "Candidate knows Python.",
            "He knows Python.",
            "It shows Python.",
            "The developer has Python.",
        ],
    )
    def test_subject_led_short_claims_are_supported(self, checker, feedback):
        """Strip a leading role or pronoun before a narrow reporting verb."""
        assert checker.check(feedback, [{"text": "Python projects"}]) == 1.0

    def test_bare_one_word_feedback_remains_unscoreable(self, checker):
        """Do not turn arbitrary one-word fragments into supported claims."""
        # Preserve main's neutral score when no claim is extracted.
        assert checker.check("Python.", [{"text": "Python projects"}]) == 0.5
        assert checker._is_supported("Python", "Python projects") is False
        assert checker._is_supported("Candidate Python", "Python projects") is False
        assert checker.check("The and that were to be.", [{"text": "anything"}]) == 0.0

    def test_context_punctuation_does_not_block_short_claim_support(self, checker):
        """Match a fact even when it ends the context sentence."""
        assert checker.check("Knows SQL.", [{"text": "Uses Python and SQL."}]) == 1.0
        assert (
            checker.check(
                "Knows Python. Knows SQL.",
                [{"text": "Uses Python.Knows SQL"}],
            )
            == 1.0
        )

    @pytest.mark.parametrize(
        "technology",
        ["Python", "Node.js", "C++", "C#", ".NET", "I/O", "R&D", "Objective-C"],
    )
    def test_no_space_sentence_boundary_still_splits_claims(self, checker, technology):
        """Split adjacent reporter-led sentences after technical identifiers."""
        assert (
            checker.check(
                f"Knows {technology}.Knows SQL.",
                [{"text": f"{technology} and SQL"}],
            )
            == 1.0
        )

    def test_claim_limit_preserves_existing_first_ten_contract(self, checker):
        """Score only the first ten extracted claims, as on main."""
        feedback = " ".join(f"Knows Skill{index}." for index in range(11))
        context = " ".join(f"Skill{index}" for index in range(10))

        assert checker.check(feedback, [{"text": context}]) == 1.0

    def test_none_chunk_does_not_hide_valid_sibling_context(self, checker):
        """Skip a malformed chunk while retaining valid evidence for #153."""
        score = checker.check(
            "Knows Python.",
            [{"text": None}, {"text": "Python projects"}],
        )

        assert score == 1.0

    @pytest.mark.parametrize(
        ("claim", "context"),
        [
            ("Python expert", "Python novice"),
            ("Uses Kubernetes", "Avoids Kubernetes"),
        ],
    )
    def test_one_shared_fact_does_not_support_material_mismatch(self, checker, claim, context):
        """Preserve the two-term overlap floor for ordinary claims."""
        assert checker._is_supported(claim, context) is False

    def test_common_technical_identifiers_remain_whole(self, checker):
        """Tokenize common symbolic and compound technology names intact."""
        assert checker._tokenize("C++ C# .NET Node.js Objective-C R&D I/O non_python") == [
            "c++",
            "c#",
            ".net",
            "node.js",
            "objective-c",
            "r&d",
            "i/o",
            "non_python",
        ]
        assert checker._extract_claims("Uses Node.js. Knows SQL.") == [
            "Uses Node.js",
            "Knows SQL",
        ]
        assert checker._is_supported("I/O systems", "O systems") is False

    @pytest.mark.parametrize("identifier", ["System.Text.Json", "Microsoft.Azure", "System.Show"])
    def test_pascal_case_dotted_identifiers_remain_whole(self, checker, identifier):
        """Do not mistake a dotted identifier for adjacent sentences."""
        assert checker._tokenize(identifier) == [identifier.casefold()]
        assert checker._extract_claims(f"Knows {identifier}. Knows SQL.") == [
            f"Knows {identifier}",
            "Knows SQL",
        ]
        assert checker.check(f"Knows {identifier}.", [{"text": identifier}]) == 1.0

    @pytest.mark.parametrize("apostrophe", ["'", "\u02bc", "\u2018", "\u2019", "\uff07"])
    def test_apostrophe_fragments_do_not_satisfy_overlap_floor(self, checker, apostrophe):
        """Keep a possessive suffix from becoming a second shared term."""
        developer = f"developer{apostrophe}s"
        candidate = f"candidate{apostrophe}s"

        assert checker._tokenize(developer) == ["developer's"]
        assert (
            checker._is_supported(
                f"The {developer} Rust work",
                f"The {candidate} Rust hobby",
            )
            is False
        )

    @pytest.mark.parametrize("hyphen", ["\u2010", "\u2011"])
    def test_compound_hyphen_fragments_do_not_satisfy_overlap_floor(self, checker, hyphen):
        """Normalize in-word hyphens without creating a shared fragment."""
        front_end = f"front{hyphen}end"
        back_end = f"back{hyphen}end"

        assert checker._tokenize(front_end) == ["front-end"]
        assert (
            checker._is_supported(
                f"{front_end} Rust work",
                f"{back_end} Rust hobby",
            )
            is False
        )
        assert checker.check(f"Knows {front_end}.", [{"text": "front-end"}]) == 1.0

    def test_very_long_feedback(self, checker):
        """Test handling of very long feedback text."""
        feedback = "The developer. " * 100
        context_chunks = [{"text": "Developer portfolio content"}]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_very_long_context(self, checker):
        """Test handling of very long context."""
        feedback = "The developer has Python skills."
        context_chunks = [{"text": "Python " * 1000}]

        score = checker.check(feedback, context_chunks)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_common_words_filtered_in_overlap(self, checker):
        """Test that common stop words are filtered in overlap calculation."""
        # This test verifies that "the", "is", "and" etc. don't count as meaningful overlap
        claim = "The project is well documented"
        context = "The project is poorly documented"  # Opposite meaning but same stop words

        supported = checker._is_supported(claim, context)

        # Lexical overlap cannot detect the contradiction, but stop words do not decide it.
        assert supported is True

    def test_role_noun_is_preserved_without_a_reporting_verb(self, checker):
        """Keep an ordinary role noun when it is part of the claim evidence."""
        assert (
            checker.check(
                "The developer is skilled.",
                [{"text": "developer skilled"}],
            )
            == 1.0
        )
        assert checker._is_supported("Their show has great production", "show production") is True

    def test_minimum_overlap_required(self, checker):
        """Test that minimum meaningful overlap is required for support."""
        claim = "Python expertise"
        context = "Python"  # Only one word match

        supported = checker._is_supported(claim, context)

        assert supported is False
        assert checker._is_supported("the and", "Python") is False
        # Preserve the original stop-word table: "with" remains a content term.
        assert checker._is_supported("Built with Python", "with Python") is True

    def test_none_context_chunk_text(self, checker):
        """Reproduce issue #153 at the checker boundary."""
        feedback = "Has Python skills"
        context_chunks = [{"text": None}]

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

    def test_missing_text_key_in_chunk(self, checker):
        """Test handling of missing 'text' key in context chunk."""
        feedback = "Has Python skills"
        context_chunks = [{"content": "Python skills"}]  # Wrong key

        score = checker.check(feedback, context_chunks)

        assert score == 0.0

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
