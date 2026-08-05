"""Check if generated feedback is supported by retrieved context."""

import re

import structlog

logger = structlog.get_logger()

# Punctuation stripped from the *edges* of a token only. Interior punctuation is
# deliberately preserved: a character-class regex such as ``[a-z0-9]+`` would
# collapse ``C++`` and ``C#`` into the same token, and shatter ``Node.js``,
# ``CI/CD`` and ``3.11`` into unrelated fragments.
_EDGE_PUNCTUATION = ".,;:!?()[]{}\"'`“”‘’…—–"

# Fraction of a claim's meaningful tokens that must appear in the context for the
# claim to count as supported. An absolute count cannot work at both ends: `>= 2`
# forces a two-token claim to match 100% of its tokens, while a long claim gets
# many chances to hit two matches incidentally.
#
# The window that satisfies every test in the suite is (0.17, 0.33]: below 0.18
# "expert in Rust systems programming" starts matching a Python/JavaScript
# context on the single token "developer"; above 0.33 "Skilled with Docker" stops
# being supported by a context that names Docker.
_SUPPORT_RATIO = 0.3

# Only the first N claims are scored. This is truncation, not sampling, so the
# count is logged: everything after it is unscored and therefore invisible.
_MAX_CLAIMS = 10

# Hoisted to module scope so it is not rebuilt on every claim comparison.
_STOP_WORDS = frozenset({
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
    'and', 'or', 'but', 'in', 'of', 'to', 'for', 'that',
})


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
            List of claims (sentences)
        """
        # Split by sentence (simple regex)
        sentences = re.split(r'[.!?]+', text)
        # Filter on word count, not character count. `len(s) > 10` dropped
        # "Uses Rust" (9 chars) while keeping "Great at Go" (11) - it selected on
        # spelling length, systematically penalising short technology names, and
        # a dropped claim is not scored 0 but vanishes, so feedback made entirely
        # of short claims returned the 0.5 neutral default.
        claims = [t for s in sentences if len((t := s.strip()).split()) >= 2]

        # Log before truncating: `claims_count` in check() is measured after the
        # slice, so it saturates at _MAX_CLAIMS and hides both the discarded
        # fragments and the unscored tail.
        logger.info(
            "faithfulness_claims_extracted",
            extracted_count=len(claims),
            dropped_count=len(sentences) - len(claims),
            unscored_count=max(0, len(claims) - _MAX_CLAIMS),
        )

        return claims[:_MAX_CLAIMS]  # Limit claims for scoring

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Normalize text into a set of meaningful tokens.

        Lowercases, splits on whitespace, strips edge punctuation and drops stop
        words and empties. Claim and context must both pass through this helper:
        the tokenizer is symmetric by contract, which is what makes ``Python.``
        in the context match ``Python`` in the claim.

        Args:
            text: Raw claim or context text

        Returns:
            Set of normalized tokens, stop words removed
        """
        return {
            stripped
            for token in text.lower().split()
            if (stripped := token.strip(_EDGE_PUNCTUATION)) and stripped not in _STOP_WORDS
        }

    @staticmethod
    def _is_supported(claim: str, context: str) -> bool:
        """Check if a claim is supported by context.

        Args:
            claim: Claim text
            context: Context text

        Returns:
            True if claim is supported
        """
        # Tokenize both sides identically, then require meaningful keyword overlap
        claim_tokens = FaithfulnessChecker._tokenize(claim)
        if not claim_tokens:
            # Punctuation-only or all-stop-word claims carry nothing to verify
            return False

        meaningful_overlap = claim_tokens & FaithfulnessChecker._tokenize(context)

        # Scale the requirement to claim length rather than using a fixed count
        return len(meaningful_overlap) / len(claim_tokens) >= _SUPPORT_RATIO
