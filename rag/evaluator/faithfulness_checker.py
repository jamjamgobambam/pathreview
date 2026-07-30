"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    def check(
        self,
        feedback: str,
        context_chunks: list[dict[str, str | None]],
    ) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text.
            context_chunks: Retrieved context chunks.

        Returns:
            Faithfulness score from 0.0 to 1.0.
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

        context_text = " ".join(chunk.get("text") or "" for chunk in context_chunks)

        supported_count = sum(self._is_supported(claim, context_text) for claim in claims)

        score = supported_count / len(claims)

        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            supported_count=supported_count,
            score=score,
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract individual claims from feedback text.

        Args:
            text: Feedback text.

        Returns:
            A list of individual claims.
        """
        sentences = re.split(r"[.!?]+", text)
        claims: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            parts = re.split(r"\s*(?:,|\band\b)\s*", sentence)

            claims.extend(part.strip() for part in parts if part.strip())

        return claims[:10]

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check whether a claim is supported by the context.

        Args:
            claim: Claim text.
            context: Context text.

        Returns:
            True when the claim has enough meaningful overlap with the context.
        """
        claim_tokens = set(re.findall(r"\b\w+\b", claim.lower()))
        context_tokens = set(re.findall(r"\b\w+\b", context.lower()))

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
            "has",
            "have",
            "had",
            "shows",
            "show",
            "demonstrates",
            "demonstrated",
        }

        meaningful_claim_tokens = claim_tokens - stop_words

        if not meaningful_claim_tokens:
            return False

        meaningful_overlap = meaningful_claim_tokens & context_tokens

        required_overlap = 1 if len(meaningful_claim_tokens) <= 4 else 2

        return len(meaningful_overlap) >= required_overlap
