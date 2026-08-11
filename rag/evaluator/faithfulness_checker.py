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
        context_text = " ".join(str(chunk.get("text") or "") for chunk in context_chunks)

        # Check each claim for support
        support_scores = []
        for claim in claims:
            support_scores.append(self._support_score(claim, context_text))

        score = sum(support_scores) / len(claims) if claims else 0.0

        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            supported_count=sum(1 for item in support_scores if item >= 0.5),
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
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]
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
        return FaithfulnessChecker._support_score(claim, context) >= 0.5

    @staticmethod
    def _support_score(claim: str, context: str) -> float:
        """Return proportional support score for a claim."""
        claim_tokens = set(FaithfulnessChecker._tokenize(claim))
        context_tokens = set(FaithfulnessChecker._tokenize(context))

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
        meaningful_claim_tokens = claim_tokens - stop_words
        meaningful_overlap = (claim_tokens & context_tokens) - stop_words

        technical_terms = {
            "aws",
            "ci",
            "django",
            "docker",
            "javascript",
            "kubernetes",
            "orm",
            "postgresql",
            "python",
            "rust",
            "sqlalchemy",
        }
        claim_technical_terms = meaningful_claim_tokens & technical_terms
        if claim_technical_terms:
            return len(claim_technical_terms & context_tokens) / len(claim_technical_terms)

        return 1.0 if len(meaningful_overlap) >= 2 else 0.0

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text into lowercase word tokens."""
        return re.findall(r"[a-z0-9+#.-]+", text.lower())
