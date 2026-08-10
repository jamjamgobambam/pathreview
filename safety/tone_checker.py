"""Heuristic classification of generated feedback tone."""

import re

import structlog

from safety.content_filter import ContentFilter

logger = structlog.get_logger()


class ToneChecker:
    """Classify generated feedback as constructive or not.

    Constructive feedback (per issue #69) is actionable, specific, and
    encouraging — not merely free of harmful or discouraging language.
    This complements ContentFilter's pattern-based flagging with checks
    for near-empty and vague content, the cases a keyword filter alone
    won't catch.
    """

    MIN_LENGTH = 20  # characters; catches near-empty or one-word feedback

    # Generic praise/filler with no specifics — technically not
    # discouraging, but not actionable either.
    VAGUE_PATTERNS = [
        r"^(?:great|good|nice|ok(?:ay)?|fine)\s*(?:job|work)?\.?$",
        r"^(?:looks?\s+good|not\s+bad)\.?$",
    ]

    @staticmethod
    def check_tone(text: str) -> tuple[bool, str]:
        """Classify feedback text as constructive or not.

        Args:
            text: Generated feedback section content

        Returns:
            Tuple of (is_constructive, reason). reason is an empty
            string when is_constructive is True.
        """
        stripped = text.strip() if text else ""

        if not stripped:
            reason = "Feedback is empty"
            logger.warning("tone_check_failed", reason=reason)
            return False, reason

        if len(stripped) < ToneChecker.MIN_LENGTH:
            reason = "Feedback is too short to be actionable"
            logger.warning("tone_check_failed", reason=reason, length=len(stripped))
            return False, reason

        # Reuse ContentFilter's harmful/discouraging patterns rather than
        # duplicating them — ordering matters here: anything ContentFilter
        # would flag is also not constructive.
        _, was_flagged = ContentFilter.filter(text)
        if was_flagged:
            reason = "Feedback contains discouraging or dismissive language"
            logger.warning("tone_check_failed", reason=reason)
            return False, reason

        for pattern in ToneChecker.VAGUE_PATTERNS:
            if re.match(pattern, stripped, re.IGNORECASE):
                reason = "Feedback is too vague to be actionable"
                logger.warning("tone_check_failed", reason=reason)
                return False, reason

        return True, ""
