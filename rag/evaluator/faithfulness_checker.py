"""Check if generated feedback is supported by retrieved context."""

import math
import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

    STOP_WORDS = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
        'and', 'or', 'but', 'in', 'of', 'to', 'for', 'that',
    }

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
        """Check faithfulness of feedback to context.

        Args:
            feedback: Generated feedback text
            context_chunks: Retrieved context chunks

        Returns:
            Faithfulness score 0.0-1.0 (average degree of support across claims)
        """
        if not feedback or not context_chunks:
            logger.info("faithfulness_empty_input", has_feedback=bool(feedback),
                      has_chunks=bool(context_chunks))
            return 0.0

        # Extract key claims from feedback (sentences)
        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5  # Default to neutral if no extractable claims

        # Concatenate context text (guard against None values, not just missing keys)
        context_text = " ".join([
            chunk.get("text") or "" for chunk in context_chunks
        ])

        # Score each claim's degree of support, then average
        claim_scores = [self._support_score(claim, context_text) for claim in claims]
        score = sum(claim_scores) / len(claim_scores)

        logger.info("faithfulness_checked", claims_count=len(claims),
                  supported_count=sum(1 for s in claim_scores if s >= 0.5), score=score)

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
        sentences = re.split(r'[.!?]+', text)
        claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Tokenize text into a set of lowercase word tokens, stripping punctuation.

        Args:
            text: Text to tokenize

        Returns:
            Set of lowercase alphanumeric tokens
        """
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    @classmethod
    def _support_score(cls, claim: str, context: str) -> float:
        """Compute a continuous degree-of-support score for a claim.

        Rather than a flat pass/fail on raw overlap count, this scores the
        fraction of the claim's own meaningful tokens that are found in the
        context, square-rooted so partial overlap isn't punished as harshly
        as a linear ratio would (a claim doesn't need 100% token overlap to
        be meaningfully supported). Short claims (few meaningful tokens) can
        still score well on a single strong match, fixing the original bug
        where any claim needed 2+ overlapping tokens no matter how short it
        was.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            Support score in the range 0.0-1.0
        """
        claim_tokens = cls._tokenize(claim)
        context_tokens = cls._tokenize(context)

        meaningful_claim_tokens = claim_tokens - cls.STOP_WORDS
        if not meaningful_claim_tokens:
            # No meaningful content in the claim to verify against context.
            return 0.0

        overlap = (claim_tokens & context_tokens) - cls.STOP_WORDS
        ratio = len(overlap) / len(meaningful_claim_tokens)

        return math.sqrt(ratio)

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim's support score meets the support threshold
        """
        return cls._support_score(claim, context) >= 0.5
