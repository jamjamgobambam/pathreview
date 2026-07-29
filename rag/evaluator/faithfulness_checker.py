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
        context_text = " ".join(
            [chunk.get("text") or "" for chunk in context_chunks if isinstance(chunk, dict)]
        )
        if not context_text:
            logger.info("faithfulness_empty_context")
            return 0.0

        # Check each claim for support
        supported = 0
        for claim in claims:
            if FaithfulnessChecker._is_supported(claim, context_text):
                supported += 1

        score = supported / len(claims) if claims else 0.0

        logger.info(
            "faithfulness_checked", claims_count=len(claims), supported_count=supported, score=score
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text."""
        if not text or not isinstance(text, str):
            return []

        # First split by major sentence boundaries
        sentences = re.split(r"[.!?]+", text)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If a sentence contains conjunctions/commas (e.g. "Python, JavaScript, and Docker"),
            # split into sub-claims so each skill is evaluated independently
            sub_parts = re.split(r",|\band\b", sentence)
            if len(sub_parts) > 1:
                for part in sub_parts:
                    part_clean = part.strip()
                    if len(part_clean) >= 3:
                        claims.append(part_clean)
            elif len(sentence) >= 3:
                claims.append(sentence)

        return claims[:10]

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context."""
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
            "with",
            "has",
            "have",
            "had",
            "shows",
            "showing",
            "demonstrates",
            "developer",
            "expertise",
            "experience",
            "skills",
            "knowledge",
        }

        # Extract clean words using regex (automatically strips commas, periods, etc.)
        claim_words = re.findall(r"\b\w+\b", claim.lower())
        context_words = re.findall(r"\b\w+\b", context.lower())

        claim_tokens = set(w for w in claim_words if w not in stop_words)
        context_tokens = set(w for w in context_words if w not in stop_words)

        if not claim_tokens:
            return False

        meaningful_overlap = claim_tokens & context_tokens

        # For short claims (1 key token like "rust"), 1 match is sufficient.
        # Otherwise require min(2, len(claim_tokens)).
        required_overlap = 1 if len(claim_tokens) <= 2 else 2

        return len(meaningful_overlap) >= required_overlap
