"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course|coding\s+bootcamp)\s+(?:education|training)\s+(?:is\s+)?(?:insufficient|inadequate|lacks?(?:\s+\w+)?)",
        r"(?:bootcamp|self-taught|coding\s+bootcamp)\s+(?:graduates?|developers?|programmers?)\s+(?:can'?t|cannot|won'?t|will\s+not|lacks?|missing)\s+\w+",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)(?:\s+(?:developers?|graduates?|programmers?))?\s+(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        r"(?:bootcamp|self-taught)\s+attendance\s+means\s+(?:insufficient|inadequate|poor|lack\s+of)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|developers?|programmers?)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:person|people|developers?|programmers?|coming)\s+from\s+(?:poor|rich|working[\s-]?class)",
        r"(?:immigrant|international|foreign)\s+(?:developers?|programmers?).*(?:can't|cannot|won't|struggle)",
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
