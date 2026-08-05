"""Regression tests for issue #152.

Faithfulness checker can never mark short claims as supported.

These tests were written against the unfixed implementation, where they
failed. They document three distinct root causes:

1. ``_is_supported`` tokenizes on whitespace only, so trailing punctuation in
   the context (``"Python."``) never matches a claim token (``"Python"``).
2. ``_is_supported`` requires an absolute ``>= 2`` meaningful-token overlap
   regardless of claim length, so a two-token claim must match 100% of its
   tokens and a one-meaningful-token claim can never be supported at all.
3. ``_extract_claims`` discards any sentence of 10 characters or fewer, so
   very short feedback yields zero claims and silently returns the 0.5
   neutral default instead of a real score.

The classes below the regression cases pin the behaviour of the pieces the fix
introduced: the shared tokenizer, the proportional threshold, the word-count
claim filter, and the extraction logging.
"""

import pytest
from structlog.testing import capture_logs

from rag.evaluator.faithfulness_checker import (
    _MAX_CLAIMS,
    _SUPPORT_RATIO,
    FaithfulnessChecker,
)


@pytest.mark.unit
class TestShortClaimsAreSupported:
    """Short but fully grounded claims must not be scored as unsupported."""

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        return FaithfulnessChecker()

    def test_punctuation_in_context_does_not_break_support(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Root cause 1: 'Python.' in context must match 'Python' in claim."""
        score = checker.check(
            "Knows Python",
            [{"text": "The candidate knows Python."}],
        )

        assert score == 1.0, "Claim is verbatim in the context; only the trailing period differs."

    def test_short_claim_with_paraphrased_context_is_supported(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Root cause 2: one strong keyword match is enough for a 2-word claim."""
        score = checker.check(
            "Knows Python",
            [{"text": "The candidate is proficient in Python and ships production services."}],
        )

        assert score == 1.0, "Context clearly grounds the claim, but only one token overlaps."

    def test_single_meaningful_token_claim_can_be_supported(
        self, checker: FaithfulnessChecker
    ) -> None:
        """Root cause 2: a claim with one meaningful token is not automatically false."""
        supported = checker._is_supported(
            "Uses Kubernetes",
            "Deployments are managed on Kubernetes.",
        )

        assert supported is True

    def test_very_short_claim_is_not_silently_dropped(self, checker: FaithfulnessChecker) -> None:
        """Root cause 3: a 9-char sentence must still be scored, not skipped."""
        score = checker.check(
            "Uses Rust",
            [{"text": "The candidate uses Rust for systems work."}],
        )

        assert score == 1.0, "Claim was dropped by the >10-character filter and fell back to 0.5."


@pytest.mark.unit
class TestExistingBehaviourPreserved:
    """Guardrails: the fix must not turn unsupported claims into supported ones."""

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        return FaithfulnessChecker()

    def test_unsupported_claim_stays_unsupported(self, checker: FaithfulnessChecker) -> None:
        score = checker.check(
            "This developer is an expert in Rust systems programming.",
            [{"text": "The developer has Python and JavaScript experience."}],
        )

        assert score == 0.0

    def test_long_supported_claim_stays_supported(self, checker: FaithfulnessChecker) -> None:
        score = checker.check(
            "The developer has strong Python skills and experience with Django.",
            [{"text": "The portfolio shows Python expertise and Django framework experience."}],
        )

        assert score == 1.0

    def test_stop_words_alone_are_not_support(self, checker: FaithfulnessChecker) -> None:
        supported = checker._is_supported(
            "The team is in the office",
            "A of to for that and or but in the",
        )

        assert supported is False


@pytest.mark.unit
class TestTokenizer:
    """The tokenizer contract: edge punctuation goes, interior punctuation stays."""

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        return FaithfulnessChecker()

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Python.", "python"),
            ("Python,", "python"),
            ('"Python"', "python"),
            ("(Python)", "python"),
            ("Python!?", "python"),
            ("'Python';", "python"),
        ],
    )
    def test_edge_punctuation_is_stripped(
        self, checker: FaithfulnessChecker, raw: str, expected: str
    ) -> None:
        """Root cause 1: punctuation clinging to a token must not defeat matching."""
        assert checker._tokenize(raw) == {expected}

    @pytest.mark.parametrize(
        "token",
        ["c++", "c#", "node.js", "ci/cd", "k8s", "3.11", "state-of-the-art", "asp.net"],
    )
    def test_interior_punctuation_is_preserved(
        self, checker: FaithfulnessChecker, token: str
    ) -> None:
        """Tech names must survive intact.

        A character-class regex such as ``[a-z0-9]+`` would collapse ``c++`` and
        ``c#`` into the same token and split the rest into fragments.
        """
        assert checker._tokenize(token) == {token}

    def test_cpp_and_csharp_do_not_collide(self, checker: FaithfulnessChecker) -> None:
        """The specific false positive that motivated edge-only stripping."""
        assert checker._tokenize("C++") != checker._tokenize("C#")
        assert checker._is_supported("Writes C++ daily", "The codebase is C# throughout") is False

    @pytest.mark.parametrize(
        "raw",
        ["“Python”", "Python…", "—Python—", "‘Python’"],
    )
    def test_unicode_punctuation_is_stripped(self, checker: FaithfulnessChecker, raw: str) -> None:
        """LLM output routinely contains curly quotes, ellipsis and dashes."""
        assert checker._tokenize(raw) == {"python"}

    def test_tokenization_is_symmetric(self, checker: FaithfulnessChecker) -> None:
        """The invariant the fix rests on: both sides go through the same tokenizer.

        Stripping only the context side is not enough - claims carry punctuation
        too, as in "Python, JavaScript, and Docker".
        """
        claim = "Python, JavaScript, and Docker"
        context = "Uses Python. Writes JavaScript! Ships Docker?"

        assert checker._tokenize(claim) == checker._tokenize(context) - {"uses", "writes", "ships"}

    def test_case_and_whitespace_are_normalized(self, checker: FaithfulnessChecker) -> None:
        assert checker._tokenize("  PYTHON\tDjango\n\nRust  ") == {"python", "django", "rust"}

    @pytest.mark.parametrize("raw", ["", "   ", "...", "!?", "the is and of"])
    def test_contentless_text_yields_no_tokens(
        self, checker: FaithfulnessChecker, raw: str
    ) -> None:
        """Punctuation-only and stop-word-only text must produce an empty set, not a crash."""
        assert checker._tokenize(raw) == set()


@pytest.mark.unit
class TestProportionalThreshold:
    """Support scales with claim length instead of using a fixed token count."""

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        return FaithfulnessChecker()

    def test_ratio_is_within_the_measured_window(self) -> None:
        """Guard the constant itself.

        Below 0.18 "expert in Rust systems programming" starts matching a
        Python/JavaScript context on the single token "developer"; above 0.33
        "Skilled with Docker" stops being supported by a context naming Docker.
        Moving _SUPPORT_RATIO outside this window breaks a maintainer test, so
        fail here with an explanation rather than there with a bare assert.
        """
        assert 0.17 < _SUPPORT_RATIO <= 0.33

    def test_one_of_two_tokens_is_enough(self, checker: FaithfulnessChecker) -> None:
        """A two-token claim no longer has to match 100% of itself."""
        assert checker._is_supported("Knows Python", "Proficient in Python") is True

    def test_one_of_six_tokens_is_not_enough(self, checker: FaithfulnessChecker) -> None:
        """The threshold still has to reject weak overlap on a long claim."""
        assert (
            checker._is_supported(
                "This developer is an expert in Rust systems programming",
                "The developer has Python and JavaScript experience.",
            )
            is False
        )

    def test_longer_claims_need_proportionally_more_evidence(
        self, checker: FaithfulnessChecker
    ) -> None:
        """The same single matching token supports a short claim but not a long one.

        This is the asymmetry the old absolute count could not express.
        """
        context = "The portfolio demonstrates Python."

        assert checker._is_supported("Knows Python", context) is True
        assert (
            checker._is_supported(
                "Knows Python plus Rust Docker Kubernetes Terraform Django", context
            )
            is False
        )

    def test_empty_claim_is_never_supported(self, checker: FaithfulnessChecker) -> None:
        """A claim with no meaningful tokens must not divide by zero."""
        assert checker._is_supported("...", "Python Django Rust") is False
        assert checker._is_supported("the and of", "the and of") is False


@pytest.mark.unit
class TestClaimExtraction:
    """Claims are selected by word count, not by how long the words are spelled."""

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        return FaithfulnessChecker()

    @pytest.mark.parametrize("claim", ["Uses Rust", "Knows Go", "Writes C", "Ships SQL"])
    def test_short_technology_claims_are_kept(
        self, checker: FaithfulnessChecker, claim: str
    ) -> None:
        """Root cause 3: the >10-character filter penalized short technology names."""
        assert checker._extract_claims(f"{claim}.") == [claim]

    @pytest.mark.parametrize("text", ["Nope.", "Yes!", "...", "   ", ""])
    def test_single_word_and_empty_fragments_are_dropped(
        self, checker: FaithfulnessChecker, text: str
    ) -> None:
        assert checker._extract_claims(text) == []

    def test_claims_are_capped(self, checker: FaithfulnessChecker) -> None:
        text = " ".join(f"Claim number {i}." for i in range(_MAX_CLAIMS + 5))

        assert len(checker._extract_claims(text)) == _MAX_CLAIMS


@pytest.mark.unit
class TestExtractionLogging:
    """Discarded and unscored input must be visible in the logs.

    ``claims_count`` in ``check()`` is measured after the ``_MAX_CLAIMS`` slice,
    so it saturates and hides both the dropped fragments and the unscored tail.
    """

    @pytest.fixture
    def checker(self) -> FaithfulnessChecker:
        return FaithfulnessChecker()

    def test_dropped_fragments_are_logged(self, checker: FaithfulnessChecker) -> None:
        with capture_logs() as logs:
            checker._extract_claims("Knows Python. Nope. Uses Rust.")

        event = next(e for e in logs if e["event"] == "faithfulness_claims_extracted")
        assert event["extracted_count"] == 2
        assert event["dropped_count"] == 2  # "Nope" and the trailing empty split artifact
        assert event["unscored_count"] == 0

    def test_unscored_tail_is_logged(self, checker: FaithfulnessChecker) -> None:
        text = " ".join(f"Claim number {i}." for i in range(_MAX_CLAIMS + 3))

        with capture_logs() as logs:
            checker._extract_claims(text)

        event = next(e for e in logs if e["event"] == "faithfulness_claims_extracted")
        assert event["extracted_count"] == _MAX_CLAIMS + 3
        assert event["unscored_count"] == 3

    def test_neutral_default_is_distinguishable_from_a_real_score(
        self, checker: FaithfulnessChecker
    ) -> None:
        """0.5 from "nothing to score" must not look like 0.5 from "half supported"."""
        with capture_logs() as logs:
            score = checker.check("Nope.", [{"text": "Some context here."}])

        assert score == 0.5
        assert any(e["event"] == "faithfulness_no_claims_extracted" for e in logs)
