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
            List of claims (sentences, further split on "and" so compound
            sentences yield independently-scored claims rather than a single
            all-or-nothing claim — see issue #152)
        """
        # Split by sentence (simple regex)
        sentences = re.split(r"[.!?]+", text)
        claims = []
        for sentence in sentences:
            # Further split compound sentences on " and " so e.g. "X and Y"
            # becomes two claims instead of one claim that can only ever
            # score fully supported or fully unsupported as a whole.
            for part in re.split(r"\s+and\s+", sentence):
                part = part.strip()
                if part and len(part) >= 10:
                    claims.append(part)
        return claims[:10]  # Limit to 10 claims for scoring

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported

        Note:
            The required overlap scales with the claim's own meaningful token
            count (with a floor of 1) rather than using a fixed threshold.
            A fixed minimum (e.g. always requiring 2 overlapping tokens)
            meant short claims with only one meaningful token could never
            be marked supported, even with a perfect context match
            (see issue #152).
        """
        # Tokenize and check for keyword overlap. Strip punctuation first so
        # commas/periods attached to a word (e.g. "Python," or "Docker.")
        # don't prevent it from matching the same word in the context.
        claim_tokens = set(re.findall(r"[a-z0-9']+", claim.lower()))
        context_tokens = set(re.findall(r"[a-z0-9']+", context.lower()))

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

        # Require at least some meaningful overlap, scaled to claim length
        overlap = claim_tokens & context_tokens
        meaningful_overlap = overlap - stop_words

        meaningful_claim_tokens = claim_tokens - stop_words
        # Require overlap of at least 20% of the claim's meaningful tokens,
        # rounded up, with a floor of 1. A flat minimum (e.g. always 2)
        # blocked short claims entirely; a flat minimum of 1 let claims
        # match on a single coincidental shared word regardless of length.
        # Scaling to length keeps short claims reachable while still
        # requiring proportionally more genuine overlap from longer ones.
        required_overlap = max(1, (len(meaningful_claim_tokens) + 4) // 5)

        return len(meaningful_overlap) >= required_overlap
