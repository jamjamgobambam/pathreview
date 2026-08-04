"""Content filter for generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class ContentFilter:
    """Filter genuinely harmful content from generated feedback."""

    # Specific harmful patterns (not broad keyword matching)
    HARMFUL_PATTERNS = [
        r"(?:kill|harm|hurt)\s+(?:yourself|yourself|themself|themselves)",
        r"(?:suicide|self-harm|cut\s+yourself)",
        r"(?:hate|despise)\s+(?:themself|themselves|yourself)",
        r"(?:worthless|useless|trash|garbage)\s+(?:person|human)",
        r"(?:illegal|unlawful)\s+(?:activity|action|conduct)",
        r"(?:child|minor)\s+(?:abuse|exploitation|trafficking)",
    ]

    # Discouraging/dismissive tone patterns (not harmful, but not constructive
    # either) — flagged rather than redacted, since rewriting them in place
    # would produce garbled feedback; the caller should regenerate instead.
    DISCOURAGING_PATTERNS = [
        r"(?:your|this)\s+(?:code|work|project|portfolio)\s+is\s+(?:sloppy|garbage|trash|terrible|awful)",
        r"didn't\s+try\s+(?:very\s+)?hard",
        r"(?:isn't|is\s+not|wasn't)\s+worth\s+(?:including|the\s+effort|your\s+time|pursuing)",
        r"amateur(?:ish)?\s+work",
        r"reflects?\s+poorly\s+on\s+you",
        r"(?:you're|you\s+are)\s+not\s+(?:cut\s+out|good\s+enough)\s+for",
        r"(?:give\s+up|quit)\s+(?:on\s+)?(?:coding|programming|this\s+career|tech)",
        r"waste\s+of\s+(?:time|effort|everyone's\s+time)",
    ]

    @staticmethod
    def filter(text: str) -> tuple[str, bool]:
        """Filter harmful content and flag discouraging tone in text.

        Args:
            text: Text to filter

        Returns:
            Tuple of (filtered_text, was_filtered). Harmful phrases are
            redacted in filtered_text; discouraging tone is flagged via
            was_filtered but left in filtered_text unchanged, since it
            should trigger regeneration rather than in-place rewriting.
        """
        was_filtered = False
        filtered_text = text

        for pattern in ContentFilter.HARMFUL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("harmful_content_detected", pattern=pattern)
                was_filtered = True
                # Replace harmful phrases with neutral text
                filtered_text = re.sub(
                    pattern, "[CONTENT REMOVED]", filtered_text, flags=re.IGNORECASE
                )

        for pattern in ContentFilter.DISCOURAGING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("discouraging_tone_detected", pattern=pattern)
                was_filtered = True

        return filtered_text, was_filtered
