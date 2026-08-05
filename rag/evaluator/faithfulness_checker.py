"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()


class FaithfulnessChecker:
    """Verify that feedback claims are supported by context."""

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
    }

    def check(self, feedback: str, context_chunks: list[dict]) -> float:
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

        supported = sum(self._is_supported(claim, context_text) for claim in claims)

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

        Short statements containing at least two words are retained.
        Sentences containing lists or conjunctions are separated into
        smaller claims.

        Args:
            text: Feedback text.

        Returns:
            Up to 10 extracted claims.
        """
        sentences = re.split(r"[.!?]+", text)
        claims: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            parts = re.split(
                r",|\band\b",
                sentence,
                flags=re.IGNORECASE,
            )

            for part in parts:
                claim = part.strip()

                if len(re.findall(r"\b\w+\b", claim)) >= 2:
                    claims.append(claim)

        return claims[:10]

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Check whether a claim has sufficient meaningful context overlap.

        Args:
            claim: Claim text.
            context: Context text.

        Returns:
            True when the context sufficiently supports the claim.
        """
        claim_tokens = set(re.findall(r"\b\w+\b", claim.lower()))
        context_tokens = set(re.findall(r"\b\w+\b", context.lower()))

        meaningful_claim_tokens = claim_tokens - cls.STOP_WORDS
        meaningful_context_tokens = context_tokens - cls.STOP_WORDS

        if not meaningful_claim_tokens:
            return False

        meaningful_overlap = meaningful_claim_tokens & meaningful_context_tokens

        overlap_count = len(meaningful_overlap)
        overlap_ratio = overlap_count / len(meaningful_claim_tokens)

        return overlap_count >= 2 or (overlap_count >= 1 and overlap_ratio >= 0.25)
