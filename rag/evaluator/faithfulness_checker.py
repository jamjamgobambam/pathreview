"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()
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
    "with",
    "has",
    "have",
    "shows",
    "show",
    "knows",
    "know",
}


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

        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5

        context_text = " ".join([chunk.get("text") or "" for chunk in context_chunks])
        ratios = [self._support_ratio(claim, context_text) for claim in claims]
        score = sum(ratios) / len(ratios) if ratios else 0.0

        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            supported_count=len(ratios),
            score=score,
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text."""
        sentences = re.split(r"[.!?]+", text)
        claims = [s.strip() for s in sentences if s.strip()]
        claims = [claim for claim in claims if len(claim.split()) >= 2]
        return claims[:10]

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Lowercase word tokens with punctuation stripped."""
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _support_ratio(self, claim: str, context: str) -> float:
        """Fraction of a claim's meaningful tokens found in the context."""
        claim_tokens = self._tokenize(claim) - STOP_WORDS
        if not claim_tokens:
            return 0.0

        context_tokens = self._tokenize(context)
        overlap = claim_tokens & context_tokens
        if not overlap:
            return 0.0

        if len(claim_tokens) < 2:
            return 1.0

        return min(1.0, (2 * len(overlap)) / len(claim_tokens))

    def _is_supported(self, claim: str, context: str) -> bool:
        """Check whether a claim is supported by context."""
        return self._support_ratio(claim, context) >= 0.5
