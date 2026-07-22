"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()

# Common stop words that don't carry claim-specific meaning.
_STOP_WORDS = {
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

# Words that are capitalized only because they open a sentence/claim,
# not because they name a specific technology or fact.
_GENERIC_SENTENCE_STARTERS = {
    "the",
    "a",
    "an",
    "this",
    "that",
    "these",
    "those",
    "it",
    "they",
    "he",
    "she",
    "we",
    "i",
    "has",
    "strong",
    "knows",
    "skilled",
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
            List of claims (sentences, further split on commas/"and" so
            short standalone facts like "Knows SQL" become their own claim)
        """
        sentences = re.split(r"[.!?]+", text)
        claims = []
        for sentence in sentences:
            for part in re.split(r",|\band\b", sentence):
                part = part.strip()
                if part and len(part) > 3:
                    claims.append(part)
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        A claim is short exactly when it has few meaningful tokens, so
        requiring a fixed absolute count of overlapping tokens (e.g. 2)
        makes such claims impossible to support. Instead, prioritize
        capitalized key terms (technology/proper nouns like "Python" or
        "SQL") and require only one to appear in the context, since a
        single matching key term is a strong support signal regardless
        of claim length.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        context_tokens = set(re.findall(r"[a-z0-9]+", context.lower()))

        words = re.findall(r"[A-Za-z0-9]+", claim)
        key_terms = {
            w.lower()
            for w in words
            if w[0].isupper() and w.lower() not in _GENERIC_SENTENCE_STARTERS
        }
        if key_terms:
            return bool(key_terms & context_tokens)

        # No capitalized key terms to anchor on: fall back to requiring
        # at least one shared non-stopword token.
        claim_tokens = set(re.findall(r"[a-z0-9]+", claim.lower()))
        meaningful = claim_tokens - _STOP_WORDS
        return bool(meaningful & context_tokens)
