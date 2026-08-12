"""Check if generated feedback is supported by retrieved context."""

import re
from typing import Any

import structlog

logger = structlog.get_logger()

# Preserve the original function-word filter. Material predicates and
# qualifiers stay out of this set so ordinary two-token claims are not
# collapsed into unsafe one-token claims.
_STOP_WORDS = frozenset(
    {
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
)

# Issue #152's short-claim exception applies to bare claims and the
# reporting forms "Knows <fact>" / "[The] candidate knows <fact>".
_SHORT_CLAIM_REPORTERS = frozenset({"know", "knows"})
_SHORT_CLAIM_SUBJECTS = frozenset({"candidate"})

# Strip ordinary punctuation so "Python," matches "python", while keeping
# common technical compounds such as Node.js, C++, and C#.
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.'\-][a-z0-9]+)*(?:\+\+|#)?", re.IGNORECASE)

# A claim counts as fully grounded once this many of its meaningful tokens
# appear in the context; longer claims never need more than this.
_FULL_SUPPORT_TOKENS = 3

# Per-claim score at or above which a claim is considered supported.
_SUPPORT_THRESHOLD = 0.5

# Ceiling (strictly below _SUPPORT_THRESHOLD) for claims that do not meet
# the support rule: partial overlap contributes to the graded score but
# never classifies a claim as supported.
_PARTIAL_SUPPORT_CAP = 0.4


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    def check(self, feedback: str, context_chunks: list[dict[str, Any]]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text
            context_chunks: Retrieved context chunks

        Returns:
            Faithfulness score 0.0-1.0 (mean per-claim support)
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

        # Aggregate context tokens across chunks; treat missing/None text as empty
        context_tokens: set[str] = set()
        for chunk in context_chunks:
            context_tokens |= self._tokenize(chunk.get("text") or "")

        claim_scores = [self._support_score(claim, context_tokens) for claim in claims]
        score = sum(claim_scores) / len(claim_scores)

        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            supported_count=sum(1 for s in claim_scores if s >= _SUPPORT_THRESHOLD),
            score=score,
        )

        return score

    @classmethod
    def _extract_claims(cls, text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of claims (sentences)
        """
        # Keep every nonempty tokenizable fragment so short claims such as
        # "Knows SQL" remain scoreable (issue #152).
        sentences = re.split(r"[.!?]+", text)
        claims = [s.strip() for s in sentences if s.strip() and cls._tokenize(s)]
        return claims[:10]  # Limit to 10 claims for scoring

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        """Tokenize text into a lowercase, punctuation-stripped token set.

        Args:
            text: Text to tokenize

        Returns:
            Set of lowercase tokens
        """
        return {token.lower() for token in _TOKEN_RE.findall(text)}

    @classmethod
    def _token_sequence(cls, text: str) -> list[str]:
        """Return tokens in source order (lowercase)."""
        return [token.lower() for token in _TOKEN_RE.findall(text)]

    @classmethod
    def _claim_terms(cls, claim: str) -> tuple[set[str], bool]:
        """Return claim terms and whether one matched term may support it.

        The one-token exception applies only to a genuinely bare claim or
        issue #152's reporting shape ("[The] candidate knows Python").
        Material predicates and qualifiers remain terms and keep the
        original two-match floor.
        """
        ordered_terms = [token for token in cls._token_sequence(claim) if token not in _STOP_WORDS]
        reporter_shape = False
        content_terms = ordered_terms

        if ordered_terms[:1] and ordered_terms[0] in _SHORT_CLAIM_REPORTERS:
            reporter_shape = True
            content_terms = ordered_terms[1:]
        elif (
            len(ordered_terms) >= 2
            and ordered_terms[0] in _SHORT_CLAIM_SUBJECTS
            and ordered_terms[1] in _SHORT_CLAIM_REPORTERS
        ):
            reporter_shape = True
            content_terms = ordered_terms[2:]

        original_terms = set(ordered_terms)
        terms = set(content_terms)
        one_token_exception = len(terms) == 1 and (reporter_shape or len(original_terms) == 1)
        return terms, one_token_exception

    @classmethod
    def _support_score(cls, claim: str, context_tokens: set[str]) -> float:
        """Score how well a claim is grounded in the context tokens.

        A claim is supported when at least two of its terms appear in the
        context — the original rule — or when one matched term is eligible
        for the narrowly scoped issue #152 exception. Unsupported claims
        keep a graded partial score capped below the support threshold.

        Args:
            claim: Claim text
            context_tokens: Tokenized context

        Returns:
            Support score 0.0-1.0
        """
        terms, one_token_exception = cls._claim_terms(claim)
        if not terms:
            return 0.0

        matched = terms & context_tokens
        short_supported = one_token_exception and len(matched) == 1
        supported = len(matched) >= 2 or short_supported

        raw = len(matched) / min(len(terms), _FULL_SUPPORT_TOKENS)
        if supported:
            return min(1.0, max(raw, _SUPPORT_THRESHOLD))
        return min(raw, _PARTIAL_SUPPORT_CAP)

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        return cls._support_score(claim, cls._tokenize(context)) >= _SUPPORT_THRESHOLD
