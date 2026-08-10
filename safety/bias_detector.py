"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+(?:is\s+(?:insufficient|inadequate)|lacks)",
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?|students?|programmers?)\s+(?:usually\s+)?(?:lack|missing)\s+(?:a\s+)?(?:strong\s+)?(?:technical\s+)?(?:foundation|rigor|fundamentals|proper\s+training)",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)\s+is\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        r"(?:bootcamp|coding\s+bootcamp)\s+graduates?\s+are\s+not\s+prepared\s+for\s+real\s+\w+\s+work",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:graduates?|developers?|programmers?)\s+(?:can't|cannot|won't)\s+(?:write|handle|build|produce)",
        r"self-taught\s+developers?\s+are\s+not\s+equal\s+to\s+university\s+graduates?",
        r"online\s+course\s+students?\s+are\s+less\s+capable\s+than\s+university\s+graduates?",
        r"bootcamp\s+attendance\s+means\s+(?:insufficient|inadequate)\s+training",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:persons?|developers?|programmers?)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:(?:persons?|developers?|programmers?)\s+from|coming\s+from)\s+(?:poor|rich|working[\s-]?class)\s+backgrounds?",
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
