"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        (
            r"(?:bootcamp|self-taught|online\s+course)\s+"
            r"(?:education|training)\s+"
            r"(?:(?:is\s+)?(?:insufficient|inadequate)|"
            r"lacks?\s+(?:rigor|fundamentals|proper\s+training))"
        ),
        (
            r"(?:coding\s+)?bootcamp\s+"
            r"(?:graduates?|developers?|programmers?)\s+"
            r"(?:can't|cannot|won't|will\s+not)\b"
        ),
        (
            r"(?:bootcamp|self-taught)\s+"
            r"(?:graduates?|developers?|programmers?)\s+"
            r"(?:lack|lacks|are\s+missing)\s+"
            r"(?:rigor|fundamentals|proper\s+training)"
        ),
        (
            r"(?:bootcamp|coding\s+bootcamp)\s+"
            r"(?:doesn't|does\s+not)\s+prepare\s+"
            r"(?:you|developers?)"
        ),
        (
            r"(?:self-taught|(?:coding\s+)?bootcamp)"
            r"(?:\s+(?:graduates?|developers?|programmers?))?\s+"
            r"(?:is|are)\s+(?:not|never)\s+"
            r"(?:equal|comparable)\s+to\s+"
            r"(?:university|traditional|formal)"
        ),
        (
            r"(?:bootcamp|self-taught|online\s+course)\s+"
            r"(?:attendance|background)\s+"
            r"(?:means|implies)\s+"
            r"(?:inadequate|insufficient)\s+"
            r"(?:education|training|preparation)"
        ),
        (
            r"(?:attended|completed|graduated\s+from)\s+"
            r"(?:a\s+)?(?:coding\s+)?bootcamp\b"
            r"[^.!?]{0,100}\b(?:lacks?|missing)\s+"
            r"(?:the\s+)?(?:rigor|fundamentals)\b"
        ),
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        (
            r"(?:young(?:er)?|old\s+aged|old(?:er)?|aged)\s+"
            r"(?:persons?|developers?|programmers?)\s+"
            r"(?:can't|cannot|won't|will\s+not)\b"
        ),
        (
            r"(?:(?:persons?|developers?|programmers?)\s+from|"
            r"coming\s+from)\s+"
            r"(?:a\s+)?(?:poor|rich|working[\s-]?class)\s+"
            r"backgrounds?\b[^.!?]{0,40}\b"
            r"(?:can't|cannot|won't|will\s+not)\b"
        ),
        (
            r"(?:immigrant|international|foreign)\s+developers?\b"
            r"[^.!?]{0,80}\b"
            r"(?:can't|cannot|won't|will\s+not|struggle)\b"
        ),
        (
            r"(?:given|because\s+of|due\s+to)\s+"
            r"(?:their|his|her|the)\s+age\b"
            r"[^.!?]{0,50}\b"
            r"(?:can't|cannot|won't|will\s+not)\b"
        ),
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
