"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()

# Common words that carry no evidence value when matching a claim against
# context. Kept small on purpose: only true function words, so domain terms
# such as "python" or "docker" are always treated as meaningful.
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
}

# Token pattern: alphanumeric runs, so trailing punctuation (e.g. "Python,")
# does not prevent a match against "python".
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text.
            context_chunks: Retrieved context chunks.

        Returns:
            Faithfulness score 0.0-1.0 (mean per-claim support across claims).
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

        # Score each claim on how well the context supports it, then average.
        # Grading each claim (instead of a hard supported/unsupported flag)
        # lets partially grounded feedback land in the middle of the range.
        total_support = 0.0
        supported = 0
        for claim in claims:
            claim_support = self._support_score(claim, context_text)
            total_support += claim_support
            if claim_support >= 0.5:
                supported += 1

        score = total_support / len(claims)

        logger.info(
            "faithfulness_checked", claims_count=len(claims), supported_count=supported, score=score
        )

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text.

        Returns:
            List of claims (sentences).
        """
        # Split by sentence (simple regex)
        sentences = re.split(r"[.!?]+", text)
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text into meaningful lowercase tokens.

        Splits on non-alphanumeric characters (so punctuation is stripped) and
        removes stop words.

        Args:
            text: Text to tokenize.

        Returns:
            Set of meaningful tokens.
        """
        tokens = _TOKEN_RE.findall(text.lower())
        return {token for token in tokens if token not in STOP_WORDS}

    def _support_score(self, claim: str, context: str) -> float:
        """Grade how well the context supports a single claim.

        A claim is fully supported (1.0) once at least half of its meaningful
        tokens appear in the context, so short claims are not penalized for
        having few tokens to match. A claim with no meaningful overlap scores
        0.0, and partial overlap scores in between.

        Args:
            claim: Claim text.
            context: Context text.

        Returns:
            Support score between 0.0 and 1.0.
        """
        claim_tokens = self._tokenize(claim)
        if not claim_tokens:
            return 0.0

        context_tokens = self._tokenize(context)
        overlap = claim_tokens & context_tokens

        # Number of matches that counts as full support. Scales with claim
        # length (about half its tokens) but never requires more than one match
        # for a very short claim.
        needed = max(1, (len(claim_tokens) + 1) // 2)
        return min(1.0, len(overlap) / needed)

    def _is_supported(self, claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text.
            context: Context text.

        Returns:
            True if the claim's support score reaches the support threshold.
        """
        return self._support_score(claim, context) >= 0.5
