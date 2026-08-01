"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()

# Common function words excluded when measuring meaningful overlap between a
# claim and its context. Kept small and lexical on purpose — the checker is a
# cheap keyword heuristic, not a semantic matcher.
STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "and",
    "or",
    "but",
    "in",
    "of",
    "to",
    "for",
    "that",
}

# Smoothing constant for graded claim support. With one grounded key term a
# claim earns partial credit (1 / (1 + 2) = 0.33); each additional grounded
# term pushes the score toward 1.0 with diminishing returns. This replaces the
# old all-or-nothing rule that required >= 2 shared terms and therefore scored
# every short, single-term claim as unsupported (issue #152).
_SUPPORT_SMOOTHING = 2

# Minimum length (in characters) for a sentence to count as a scorable claim.
# Low enough to keep genuinely short claims like "Knows SQL", high enough to
# drop stray punctuation fragments left behind by sentence splitting.
_MIN_CLAIM_LEN = 3

# Word tokens: runs of letters/digits, which strips attached punctuation so
# "Python," and "python" compare equal.
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text.
            context_chunks: Retrieved context chunks.

        Returns:
            Faithfulness score 0.0-1.0 (mean per-claim support).
        """
        if not feedback or not context_chunks:
            logger.info(
                "faithfulness_empty_input",
                has_feedback=bool(feedback),
                has_chunks=bool(context_chunks),
            )
            return 0.0

        # Extract key claims from feedback (sentences)
        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5  # Default to neutral if no extractable claims

        # Concatenate context text, tolerating missing/None chunk text.
        context_text = " ".join((chunk.get("text") or "") for chunk in context_chunks)

        # Average the graded support of each claim.
        scores = [self._support_score(claim, context_text) for claim in claims]
        score = sum(scores) / len(scores)

        logger.info("faithfulness_checked", claims_count=len(claims), score=score)

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text.

        Returns:
            List of claims (sentences), capped at 10.
        """
        # Split by sentence (simple regex)
        sentences = re.split(r"[.!?]+", text)
        claims = [s.strip() for s in sentences if len(s.strip()) >= _MIN_CLAIM_LEN]
        return claims[:10]  # Limit to 10 claims for scoring

    @classmethod
    def _meaningful_tokens(cls, text: str) -> set[str]:
        """Return the set of meaningful (non-stopword) tokens in ``text``.

        Args:
            text: Text to tokenize; may be empty.

        Returns:
            Lowercased word tokens with stop words removed.
        """
        if not text:
            return set()
        return {token for token in _TOKEN_RE.findall(text.lower()) if token not in STOP_WORDS}

    @classmethod
    def _support_score(cls, claim: str, context: str) -> float:
        """Grade how well ``context`` supports ``claim``.

        The score grows with the number of meaningful tokens the claim shares
        with the context, with diminishing returns, so a single shared term
        yields partial support rather than none.

        Args:
            claim: Claim text.
            context: Context text.

        Returns:
            Support score in the range 0.0-1.0.
        """
        claim_tokens = cls._meaningful_tokens(claim)
        if not claim_tokens:
            return 0.0

        overlap = len(claim_tokens & cls._meaningful_tokens(context))
        if overlap == 0:
            return 0.0

        return overlap / (overlap + _SUPPORT_SMOOTHING)

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Check if a claim has any meaningful support in the context.

        Args:
            claim: Claim text.
            context: Context text.

        Returns:
            True if the claim shares at least one meaningful token with the
            context.
        """
        return cls._support_score(claim, context) > 0.0
