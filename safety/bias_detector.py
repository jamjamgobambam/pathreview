"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|coding\s+bootcamp|self-taught|online\s+course)\b.*\b(?:lacks?|lacking|insufficient|inadequate|poor|weak|not\s+up\s+to|can't|cannot|won't|doesn't|does\s+not|lack|missing|struggle|not\s+equal|not\s+comparable|never\s+comparable)\b",
        r"(?:bootcamp|coding\s+bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?)\b.*\b(?:can't|cannot|won't|lack|lacks|missing|struggle|are\s+not|are\s+never|doesn't|does\s+not)\b",
        r"(?:bootcamp|coding\s+bootcamp)\b.*\b(?:doesn't|does\s+not|cannot|can't|won't)\s+prepare\b",
        r"(?:self-taught|bootcamp)\b.*\b(?:is|are|being)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)\b",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged|elderly|older|younger)\s+(?:person|developers?|programmers?|engineers?|candidates?|professionals?)\b.*\b(?:can't|cannot|won't|struggle|lack|unable|is\s+not|are\s+not)\b",
        r"(?:person|developer|developers?|programmer|programmers?|candidate|candidates?)\s+(?:from|with)\s+(?:poor|rich|working[\s-]?class)\s+(?:background|backgrounds?)\b.*\b(?:can't|cannot|won't|struggle|lack|unable|is\s+not|are\s+not)\b",
        r"(?:immigrant|international|foreign)\s+(?:developers?|programmers?|candidates?|people?)\b.*\b(?:can't|cannot|won't|struggle|lack|unable|are\s+not|aren't)\b",
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
