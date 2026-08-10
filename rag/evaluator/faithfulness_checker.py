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
        # supported = 0
        # for claim in claims:
        #     if self._is_supported(claim, context_text):
        #         supported += 1

        # score = supported / len(claims) if claims else 0.0

        total_support = sum(self._support_score(claim, context_text) for claim in claims)
        score = total_support / len(claims) if claims else 0.0

        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            total_support=total_support,
            score=score,
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

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        # Tokenize and check for keyword overlap
        # claim_tokens = set(claim.lower().split())
        # context_tokens = set(context.lower().split())

        # Change: Strip punctuation before tokenizing

        claim_tokens = set(re.findall(r"[a-z0-9']+", claim.lower()))
        context_tokens = set(re.findall(r"[a-z0-9']+", context.lower()))

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

        return len(meaningful_overlap) >= 2

    @staticmethod
    def _support_score(claim: str, context: str) -> float:
        """Score how well a claim is supported by context (partial credit).

        Claims with only 1-2 content words can never reach a flat
        overlap requirement of 2, even when fully correct. This scales
        the number of overlaps needed to the claim's own length,
        capped at 3, so short claims aren't held to the same bar as
        long ones. Claims with many content words still need several
        real matches, not just one coincidental shared word, to score
        highly.
        """
        claim_tokens = set(re.findall(r"[a-z0-9']+", claim.lower()))
        context_tokens = set(re.findall(r"[a-z0-9']+", context.lower()))

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
        meaningful_claim_tokens = claim_tokens - stop_words
        if not meaningful_claim_tokens:
            return 0.0

        overlap = claim_tokens & context_tokens
        meaningful_overlap = overlap - stop_words

        required = min(3, len(meaningful_claim_tokens))
        return min(1.0, len(meaningful_overlap) / required)
