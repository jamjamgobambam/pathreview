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
            logger.info("faithfulness_empty_input", has_feedback=bool(feedback),
                       has_chunks=bool(context_chunks))
            return 0.0

        # Extract key claims from feedback (sentences)
        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5  # Default to neutral if no extractable claims

        # Concatenate context text
        context_text = " ".join([
            chunk.get("text", "") for chunk in context_chunks
        ])

        # Check each claim for support
        supported = 0
        for claim in claims:
            if self._is_supported(claim, context_text):
                supported += 1

        score = supported / len(claims) if claims else 0.0

        logger.info("faithfulness_checked", claims_count=len(claims),
                   supported_count=supported, score=score)

        return score

    @staticmethod
    def _extract_claims(text: str) -> list[str]:
        """Extract key claims from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of claims (sentences or segments)
        """
        # Split by sentence (simple regex)
        sentences = re.split(r'[.!?]+', text)
        claims: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Split compound claims into shorter segments by commas and conjunctions.
            segments = re.split(r'\s*(?:,|and|or)\s*', sentence)
            for segment in segments:
                segment = segment.strip()
                if segment and len(segment) > 3:
                    claims.append(segment)

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
        claim_tokens = set(re.findall(r"\b\w+\b", claim.lower()))
        context_tokens = set(re.findall(r"\b\w+\b", context.lower()))

        # Filter out common stop words and generic claim terms
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'and', 'or', 'but', 'in', 'of', 'to', 'for', 'that'
        }
        generic_claim_terms = {
            'developer', 'candidate', 'has', 'have', 'knows', 'know',
            'experienced', 'experience', 'expert', 'expertise', 'skills',
            'skill', 'knowledge', 'familiar', 'proficient', 'skilled',
            'shows', 'demonstrated', 'demonstrates', 'with', 'working',
            'works', 'background'
        }

        claim_meaningful = claim_tokens - stop_words
        context_meaningful = context_tokens - stop_words
        overlap = claim_meaningful & context_meaningful
        claim_core = claim_meaningful - generic_claim_terms

        if not claim_meaningful:
            return False

        if len(claim_core) <= 1:
            # Short or fact-focused claims may be supported by a single strong term.
            return len(overlap) >= 1

        # Longer claims should have at least two meaningful overlaps.
        return len(overlap) >= 2
