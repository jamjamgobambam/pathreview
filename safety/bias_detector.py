"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+(?:is\s+)?(?:(?:insufficient|inadequate)\b|lacks?\s+(?:rigor|fundamentals|proper\s+training))",
        r"(?:bootcamp|coding\s+bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?)\s+(?:(?:can't|cannot|won't|will\s+not)\s+(?:write|handle|code)|(?:lack|lacks|missing)\s+(?:rigor|fundamentals|proper\s+training))",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)(?:\s+developers?)?\s+(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)(?:\s+(?:education|graduates?))?",
        r"bootcamp\s+attendance\s+means\s+(?:inadequate|insufficient)\b\s+(?:training|education)",
        r"only\s+attended\s+a\s+bootcamp[^.!?]{0,80}lacks?\s+(?:the\s+)?rigor\s+of\s+(?:a\s+)?formal\s+(?:cs\s+)?education",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|people|developers?|programmers?)\s+(?:can't|cannot|won't|will\s+not)",
        r"given\s+their\s+age,?\s+(?:they\s+)?(?:likely\s+)?(?:can't|cannot|won't|will\s+not)\s+(?:keep\s+up|learn|handle)",
        r"(?:person|people|developers?|programmers?)\s+from\s+(?:poor|rich|working[\s-]?class)\s+backgrounds?[^.!?]{0,80}(?:can't|cannot|won't|will\s+not|struggle|lack|lacks)",
        r"coming\s+from\s+(?:poor|rich|working[\s-]?class)\s+backgrounds?[^.!?]{0,80}(?:can't|cannot|won't|will\s+not|struggle|lack|lacks)",
        r"(?:immigrant|international|foreign)\s+developers?[^.!?]{0,80}(?:can't|cannot|won't|will\s+not|struggle|lack|lacks)",
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
