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

        # Concatenate context text, guarding against malformed chunks
        context_text = " ".join(self._safe_chunk_text(chunk) for chunk in context_chunks)

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
    def _safe_chunk_text(chunk: object) -> str:
        """Safely extract text from a context chunk, tolerating malformed input.

        Handles three failure modes seen in issue #153: chunks that aren't
        dicts, missing/None "text" fields, and "text" fields of an
        unexpected type (e.g. an int).

        Args:
            chunk: A context chunk, expected to be a dict with a "text" key

        Returns:
            The chunk's text as a string, or "" if it can't be extracted
        """
        if not isinstance(chunk, dict):
            logger.warning("faithfulness_invalid_chunk_type", chunk_type=type(chunk).__name__)
            return ""

        text = chunk.get("text")

        if text is None:
            return ""

        if not isinstance(text, str):
            logger.warning(
                "faithfulness_invalid_text_type",
                text_type=type(text).__name__,
            )
            return ""

        return text

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
        claim_tokens = set(claim.lower().split())
        context_tokens = set(context.lower().split())

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
