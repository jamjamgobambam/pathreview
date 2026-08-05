"""Bias detection in generated feedback."""

import re
import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+(?:is\s+)?(?:insufficient|inadequate|lacks)",
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?)\s+(?:can't|cannot|won't|lacks?|missing)\s+(?:write|handle|rigor|fundamentals|proper\s+training)",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)(?:\s+developers?|\s+graduates?|\s+programmers?)?\s+(?:is|are)\s+not\s+equal\s+to\s+(?:university|traditional|formal)",
        r"(?:self-taught|bootcamp)\s+is\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        r"bootcamp\s+attendance\s+means\s+inadequate\s+training",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|developers?|programmers?)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:person|developers?|candidates?|people)\s+from\s+(?:poor|rich|working[\s-]?class)",
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
