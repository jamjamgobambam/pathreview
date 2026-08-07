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
            logger.info("faithfulness_empty_input", has_feedback=bool(feedback),
                       has_chunks=bool(context_chunks))
            return 0.0

        # Extract key claims from feedback (sentences)
        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5  # Default to neutral if no extractable claims

        # Concatenate context text
        context_text = " ".join([
            chunk.get("text", "") for chunk in context_chunks
        ])

        # Check each claim for support
        supported = 0
        for claim in claims:
            if self._is_supported(claim, context_text):
                supported += 1

        score = supported / len(claims) if claims else 0.0

        logger.info("faithfulness_checked", claims_count=len(claims),
                   supported_count=supported, score=score)

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
        sentences = re.split(r'[.!?]+', text)
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        # Tokenize and check for keyword overlap
        claim_tokens = set(claim.lower().split())
        context_tokens = set(context.lower().split())

        # Filter out common stop words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                     'and', 'or', 'but', 'in', 'of', 'to', 'for', 'that'}
        meaningful_claim_tokens = claim_tokens - stop_words
        if not meaningful_claim_tokens:
            # A claim with nothing but stop words has nothing to verify.
            return False

        # Require at least some meaningful overlap
        overlap = claim_tokens & context_tokens
        meaningful_overlap = overlap - stop_words

        # Scale the required overlap down for short claims: a fixed 2-word
        # bar can never be met by a claim built from 1-3 meaningful tokens
        # (issue #152), since the claim's own filler tokens (e.g. "knows")
        # count against it. Require roughly half the claim's meaningful
        # tokens to overlap, floored at 1 match and capped at the original 2.
        required = min(2, max(1, len(meaningful_claim_tokens) // 2))

        return len(meaningful_overlap) >= required
