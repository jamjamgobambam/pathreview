"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    # Common stop words, plus domain-generic terms ("developer") and filler
    # pronouns ("it") that show up in nearly every claim/context in this
    # portfolio-feedback context and so carry no discriminating signal.
    _STOP_WORDS = {
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
        "it",
        "its",
        "developer",
    }

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text
            context_chunks: Retrieved context chunks

        Returns:
            Faithfulness score 0.0-1.0 (average per-claim support)
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

        # Concatenate context text
        context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])

        # Score each claim's support and average across claims. Using a
        # proportional per-claim score (rather than a hard supported/unsupported
        # count) lets a claim with partial keyword overlap contribute a partial
        # score instead of being all-or-nothing.
        total_score = sum(self._claim_support_score(claim, context_text) for claim in claims)
        score = total_score / len(claims)

        logger.info(
            "faithfulness_checked", claims_count=len(claims), total_score=total_score, score=score
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of claims (sentences)
        """
        # Split by sentence (simple regex)
        sentences = re.split(r"[.!?]+", text)
        # Fix #152: previously required len(s.strip()) > 10, which silently
        # dropped short-but-valid claims (e.g. "Knows SQL", 9 chars) before
        # they were ever scored. Only truly empty fragments are filtered now.
        claims = [s.strip() for s in sentences if s.strip()]
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text into lowercase word tokens, ignoring punctuation."""
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    @classmethod
    def _meaningful_overlap(cls, claim: str, context: str) -> tuple[set[str], set[str]]:
        """Return (claim's meaningful tokens, overlap with context's meaningful tokens)."""
        claim_meaningful = cls._tokenize(claim) - cls._STOP_WORDS
        context_meaningful = cls._tokenize(context) - cls._STOP_WORDS
        return claim_meaningful, claim_meaningful & context_meaningful

    @staticmethod
    def _required_overlap(claim_meaningful: set[str]) -> int:
        """Minimum meaningful-token overlap needed to consider a claim supported.

        Fix #152: the overlap requirement now scales with the claim's own
        meaningful-token count instead of a fixed 2, so a short claim with only
        one or two meaningful tokens (e.g. "Knows Python" -> {"knows", "python"})
        can still be fully supported by a single strong match, while longer
        claims keep the original bar of 2.
        """
        return 1 if len(claim_meaningful) <= 2 else 2

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        claim_meaningful, overlap = cls._meaningful_overlap(claim, context)
        if not claim_meaningful:
            return False
        return len(overlap) >= cls._required_overlap(claim_meaningful)

    @classmethod
    def _claim_support_score(cls, claim: str, context: str) -> float:
        """Proportional support score for a claim, in [0.0, 1.0].

        A claim that meets `_required_overlap` scores 1.0 (fully supported);
        a claim with some but insufficient overlap scores proportionally
        rather than 0, so `check()` can reflect partial support even when
        feedback is a single sentence (one claim).
        """
        claim_meaningful, overlap = cls._meaningful_overlap(claim, context)
        if not claim_meaningful:
            return 0.0
        required = cls._required_overlap(claim_meaningful)
        return min(1.0, len(overlap) / required)
