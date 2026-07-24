"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?i)\b(?:(bootcamp|self-taught|online course)\b\W+(?:\w+\W+){0,2}(insufficient|inadequate|(lacks rigor|fundamentals|proper\s+training))\b|(insufficient|inadequate|(lacks rigor|fundamentals|proper\s+training))\b\W+(?:\w+\W+){0,2}(bootcamp|self-taught\b))",
        r"(?i)\b(?:(bootcamp|coding bootcamp)\b\W+(?:\w+\W+){0,6}(doesn't|does not|can not|can't)\b\W+(?:\w+\W+){0,6}(prepare|code)\b\W+(?:\w+\W+){0,6}(developers|you)|(developers|you)\b\W+(?:\w+\W+){0,6}(aren't|are not)\b\W+(?:\w+\W+){0,6}(bootcamp|coding bootcamp|code\b))",
        r"(?i)\b(?:(bootcamp|coding bootcamp|self-taught)\b\W+(?:\w+\W+){0,6}(is|not)\b\W+(?:\w+\W+){0,6}(equal|comparable)\b\W+(?:\w+\W+){0,6}(university|traditional|formal))",
        r"(?i)\b(?:(bootcamp)\b\W+(?:\w+\W+){0,6}(graduates|developers|programmers)\b\W+(?:\w+\W+){0,6}(can not|can't|lack)\b\W+(?:\w+\W+){0,6}(code|training)\b)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?i)\b(?:(young|old|aged)\b\W+(?:\w+\W+){0,6}(graduates|developers|developers|person|programmer)\b\W+(?:\w+\W+){0,6}(can not|can't|won't|will not)\b\W+(?:\w+\W+){0,6}(handle|code|learn)\b)",
        r"(?i)\b(?:\w+\W+){0,6}(person|developers)\b\W+(?:\w+\W+){0,6}(|from|coming|(coming from))\b\W+(?:\w+\W+){0,6}(poor|working class)\b\W+(?:\w+\W+){0,6}(can't|won't)\b",
        r"(?i)\b(?:(immigrant|international|foreign)\b\W+(?:\w+\W+){0,6}(struggle|can't|cannot|won't)\b\W+(?:\w+\W+){0,6}(code|coding|codebases))\b",
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
