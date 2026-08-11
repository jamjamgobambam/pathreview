"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

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
        context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])

        # Check each claim for support
        supported = 0
        for claim in claims:
            if self._is_supported(claim, context_text):
                supported += 1

        score = supported / len(claims) if claims else 0.0

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

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        A claim is supported when the meaningful (non-stop-word) tokens it
        shares with the context meet a length-aware threshold. The required
        overlap scales with the number of meaningful tokens in the claim,
        capped at two: a claim with a single meaningful token only needs that
        token to appear in the context, while longer claims still require two
        overlapping tokens. This prevents short but genuinely grounded claims
        from being permanently scored as unsupported.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
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

        # Tokenize and keep only meaningful (non-stop-word) claim tokens
        claim_tokens = set(claim.lower().split()) - stop_words
        context_tokens = set(context.lower().split())

        # A claim with no meaningful tokens (all stop words) cannot be supported
        if not claim_tokens:
            return False

        meaningful_overlap = claim_tokens & context_tokens

        # Scale the required overlap with the claim's length so short claims
        # are not penalized. Longer claims still need at least two overlaps.
        required = min(2, len(claim_tokens))
        return len(meaningful_overlap) >= required
