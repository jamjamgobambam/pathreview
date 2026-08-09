"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Reusable regex fragments for education and demographic bias patterns
    _EDU_SOURCE = r"(?:(?:coding\s+)?bootcamp|self-taught|online\s+course)"
    _ROLE = r"(?:graduates?|developers?|programmers?)"
    _DISMISSAL_VERB = (
        r"(?:can't|cannot|won't|will\s+not|lack(?:s|ing)?|missing|are\s+not\s+equal\s+to)"
    )
    _DEMOGRAPHIC_ROLE = r"(?:people?|persons?|developers?|programmers?)"
    _SOCIOECONOMIC_BACKGROUND = r"(?:poor|rich|working[\s-]?class)"

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        rf"{_EDU_SOURCE}\s+(?:education|training)\s+(?:is\s+)?(?:insufficient|inadequate|lacks(?:\s+(?:rigor|fundamentals|proper\s+training))?)",
        rf"{_EDU_SOURCE}\s+{_ROLE}\s+{_DISMISSAL_VERB}",
        rf"{_EDU_SOURCE}\s+{_ROLE}\s+(?:lack|missing)\s+(?:rigor|fundamentals|proper\s+training)",
        rf"{_EDU_SOURCE}\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|{_ROLE})",
        rf"{_EDU_SOURCE}\s+(?:{_ROLE}\s+)?(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        rf"{_EDU_SOURCE}\s+(?:attendance|background|experience)\s+means\s+(?:inadequate|insufficient)",
        r"(?:only\s+attended\s+(?:a\s+)?bootcamp|bootcamp\s+(?:background|graduate)).*(?:lacks?\s+(?:the\s+)?rigor|formal\s+(?:CS\s+)?education)",
        r"lacks?\s+(?:the\s+)?rigor\s+of\s+(?:a\s+)?formal\s+(?:CS\s+)?education.*(?:bootcamp|self-taught)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        rf"(?:young|old|aged)\s+{_DEMOGRAPHIC_ROLE}\s+(?:can't|cannot|won't|will\s+not)",
        rf"(?:(?:person|developer|programmer)s?\s+from|coming\s+from)\s+{_SOCIOECONOMIC_BACKGROUND}(?:\s+backgrounds?)?",
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
