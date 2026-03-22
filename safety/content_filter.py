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

    @staticmethod
    def filter(text: str) -> tuple[str, bool]:
        """Filter harmful content from text.

        Args:
            text: Text to filter

        Returns:
            Tuple of (filtered_text, was_filtered)
        """
        was_filtered = False
        filtered_text = text

        for pattern in ContentFilter.HARMFUL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("harmful_content_detected", pattern=pattern)
                was_filtered = True
                # Replace harmful phrases with neutral text
                filtered_text = re.sub(pattern, "[CONTENT REMOVED]", filtered_text, flags=re.IGNORECASE)

        return filtered_text, was_filtered
