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

        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5

        # Convert missing or None context values to empty strings.
        context_text = " ".join(str(chunk.get("text") or "") for chunk in context_chunks)

        supported = 0
        for claim in claims:
            if self._is_supported(claim, context_text):
                supported += 1

        score = supported / len(claims)

        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            supported_count=supported,
            score=score,
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract individual claims from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of sentence- or clause-level claims
        """
        parts = re.split(
            r"[.!?]+|,|\b(?:and|or|but)\b",
            text,
            flags=re.IGNORECASE,
        )

        claims = []
        for part in parts:
            claim = part.strip()
            if claim and re.search(r"\w", claim):
                claims.append(claim)

        return claims[:10]

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check whether a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if the claim has sufficient meaningful overlap with context
        """
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

        claim_tokens = set(re.findall(r"\b\w+\b", claim.lower()))
        context_tokens = set(re.findall(r"\b\w+\b", context.lower()))

        meaningful_claim = claim_tokens - stop_words
        meaningful_context = context_tokens - stop_words
        meaningful_overlap = meaningful_claim & meaningful_context

        if not meaningful_claim:
            return False

        # Short claims may have only one meaningful technical term.
        if len(meaningful_claim) <= 3:
            return len(meaningful_overlap) >= 1

        # Longer claims require proportional overlap.
        return len(meaningful_overlap) / len(meaningful_claim) >= 0.2
