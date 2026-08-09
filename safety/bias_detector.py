"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+(?:is\s+)?(?:insufficient|inadequate|lacks)",
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?)\s+(?:lack|missing|can't|cannot)\s+(?:rigor|fundamentals|proper\s+training|write|handle)",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)(?:\s+(?:developers?|graduates?|programmers?))?\s+(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        r"bootcamp\s+attendance\s+(?:means|implies|leads\s+to|results\s+in)\s+(?:inadequate|insufficient)\s+training",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|people|developer|developers|programmer|programmers)\s+(?:can't|cannot|won't|will\s+not|struggle|handle)",
        r"(?:person|people|developers?|programmers?)\s+(?:from|coming\s+from)\s+(?:poor|rich|working[\s-]?class)",
        r"(?:immigrant|international|foreign)\s+developers?.*(?:can't|cannot|won't|struggle|lack)",
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
