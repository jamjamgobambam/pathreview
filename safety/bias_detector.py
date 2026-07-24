"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?i)\b(?:(bootcamp|self-taught|online course)\b\W+(?:\w+\W+){0,6} \
            (insufficient|inadequate|(lacks rigor|fundamentals|proper\s+training))\b\
            |(insufficient|inadequate|(lacks rigor|fundamentals|proper\s+training))\b\
            \W+(?:\w+\W+){0,6}(bootcamp|self-taught\b))",
        r"(?i)\b(?:(bootcamp|coding bootcamp)\b\W+(?:\w+\W+){0,6}(doesn't|does not|can not|can't)\b\
            \W+(?:\w+\W+){0,6}(prepare|code)\b\W+(?:\w+\W+){0,6}(developers|you)|(developers|you)\b\
            \W+(?:\w+\W+){0,6}(aren't|are not)\b\W+(?:\w+\W+){0,6}\
            (bootcamp|coding bootcamp|code\b))",
        r"(?i)\b(?:(bootcamp|coding bootcamp|self-taught)\b\W+(?:\w+\W+){0,6}(is|not)\b\
            \W+(?:\w+\W+){0,6}(equal|comparable)\b\W+(?:\w+\W+){0,6}(university|traditional|formal))",
        r"(?i)\b(?:(bootcamp)\b\W+(?:\w+\W+){0,6}(graduates|developers)\b\W+(?:\w+\W+){0,6}\
            (can not|can't)\b\W+(?:\w+\W+){0,6}(code)\b)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|developer|programmer)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:person\s+from|coming\s+from)\s+(?:poor|rich|working[\s-]?class)",
        r"(?:immigrant|international|foreign)\s+developers?.*(?:can't|cannot|won't|struggle)",
    ]

    @staticmethod
    def detect_bias(text: str) -> tuple[bool, str]:
        """Detect biased language in feedback.

        Args:
            text: Feedback text

        Returns:
            Tuple of (is_biased, reason)
        """
        # Check for dismissive language about education
        for pattern in BiasDetector.DISMISSIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                reason = "Dismissive language about educational background"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        # Check for demographic assumptions
        for pattern in BiasDetector.DEMOGRAPHIC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                reason = "Demographic assumptions detected"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        return False, ""
