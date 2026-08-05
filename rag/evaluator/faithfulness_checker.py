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
        context_text = " ".join(chunk.get("text") or "" for chunk in context_chunks)

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
        # Treat sentence, conjunction, and list boundaries as separate claims so
        # mixed feedback can receive partial credit.
        fragments = re.split(r"[.!?]+|\s*,\s*|\s+and\s+", text, flags=re.IGNORECASE)
        claims = [
            fragment.strip()
            for fragment in fragments
            if fragment.strip() and re.search(r"[A-Za-z0-9]", fragment)
        ]
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
        # Normalize punctuation and casing before checking keyword overlap.
        token_pattern = r"[a-z0-9]+(?:[+#./-][a-z0-9+#./-]*)?"
        claim_tokens = set(re.findall(token_pattern, claim.lower()))
        context_tokens = set(re.findall(token_pattern, context.lower()))

        # Require at least some meaningful overlap
        overlap = claim_tokens & context_tokens
        # Filter out common stop words
        generic_words = {
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
            "had",
            "shows",
            "shown",
            "demonstrated",
            "developer",
            "project",
            "projects",
            "portfolio",
            "experience",
            "experienced",
            "expert",
            "expertise",
            "skill",
            "skills",
            "knowledge",
            "strong",
            "documented",
        }
        meaningful_overlap = overlap - generic_words

        return bool(meaningful_overlap)
