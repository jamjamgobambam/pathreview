"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    # Minimum fraction of a claim's meaningful tokens that must be covered by
    # the context for that claim to count as supported.
    SUPPORT_THRESHOLD = 0.35

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text
            context_chunks: Retrieved context chunks

        Returns:
            Faithfulness score 0.0-1.0 (ratio of supported claims)
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
        context_text = " ".join([chunk.get("text") or "" for chunk in context_chunks])

        # Score each claim on a gradient around the support threshold, rather
        # than a strict supported/unsupported count, so a single claim isn't
        # forced to a score of exactly 0.0 or 1.0.
        supported = 0
        claim_scores = []
        for claim in claims:
            ratio = self._support_ratio(claim, context_text)
            if ratio >= self.SUPPORT_THRESHOLD:
                supported += 1
            claim_scores.append(self._scale_ratio(ratio))

        score = sum(claim_scores) / len(claim_scores)

        logger.info(
            "faithfulness_checked", claims_count=len(claims), supported_count=supported, score=score
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
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims[:10]  # Limit to 10 claims for scoring

    @classmethod
    def _scale_ratio(cls, ratio: float) -> float:
        """Rescale an overlap ratio onto 0.0-1.0 so it lines up with _is_supported.

        Piecewise-linear: [0, SUPPORT_THRESHOLD) maps onto [0, 0.5) and
        [SUPPORT_THRESHOLD, 1] maps onto [0.5, 1], so a ratio of exactly
        SUPPORT_THRESHOLD (the _is_supported boundary) always scores 0.5,
        a ratio of 0 always scores 0.0, and a ratio of 1 always scores 1.0
        (no floor inflation, no saturation before the top of the range).

        Args:
            ratio: Raw overlap ratio from _support_ratio, in [0.0, 1.0]

        Returns:
            Rescaled score in [0.0, 1.0]
        """
        threshold = cls.SUPPORT_THRESHOLD
        if ratio < threshold:
            return 0.5 * (ratio / threshold)
        return 0.5 + 0.5 * (ratio - threshold) / (1 - threshold)

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        return cls._support_ratio(claim, context) >= cls.SUPPORT_THRESHOLD

    @staticmethod
    def _support_ratio(claim: str, context: str) -> float:
        """Compute the fraction of a claim's meaningful tokens covered by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            Overlap ratio 0.0-1.0 (0.0 if the claim has no meaningful tokens)
        """
        # Tokenize (stripping sentence punctuation so "python," matches
        # "python", while keeping terms like "c++" and "ci/cd" intact) and
        # check for keyword overlap
        token_pattern = r"[a-z0-9']+(?:[+/#]+[a-z0-9']*)*"
        claim_tokens = set(re.findall(token_pattern, claim.lower()))
        context_tokens = set(re.findall(token_pattern, context.lower()))

        # Require at least some meaningful overlap
        overlap = claim_tokens & context_tokens
        # Filter out common stop words
        stop_words = {
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
        meaningful_overlap = overlap - stop_words
        meaningful_claim_tokens = claim_tokens - stop_words

        return (
            len(meaningful_overlap) / len(meaningful_claim_tokens)
            if meaningful_claim_tokens
            else 0.0
        )
