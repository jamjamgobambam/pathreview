"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    SOURCE = r"(?:(?:coding\s+)?bootcamp|self-taught|online\s+(?:course)?)"
    PERSON = r"(?:graduates?|developers?|programmers?|person|people)"
    NEG_QUALITY = r"(?:insufficient|inadequate|lack|lacking|lacks)"
    DESIRED_PROPERTY = r"(?:code|rigor|fundamentals|(?:proper\s+)?training|preparation)"
    # Excludes sentence terminators and newlines so cross-topic text can't bridge a match.
    GAP = r"(?:[^.!?\n])"

    DISMISSIVE_PATTERNS = [
        rf"(?:{SOURCE})\s+(?:education|training)\s+(?:is\s+)?{NEG_QUALITY}",
        rf"(?:{SOURCE})\s+{PERSON}\s+"
        rf"(?:lacks?|missing|can't|cannot)\s+(?:write\s+|handle\s+)?"
        rf"(?:(?:production\s+|enterprise\s+)?{DESIRED_PROPERTY}|(?:production\s+|complex\s+)?systems)",
        rf"(?:{SOURCE})\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        rf"(?:{SOURCE})(?:\s+{PERSON})?\s+"
        rf"(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        rf"(?:{SOURCE})\s+attendance\s+means\s+{NEG_QUALITY}\s+{DESIRED_PROPERTY}",
        rf"(?:{SOURCE})\b"
        rf"{GAP}{{0,30}}?\b(?:so|because|since|thus|therefore|which\s+means)\b{GAP}{{0,30}}?\b"
        rf"{NEG_QUALITY}\s+"
        rf"(?:the\s+)?{DESIRED_PROPERTY}\b",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        rf"(?:young|old|aged)\s+(?:{PERSON})\s+(?:can't|cannot|won't|will\s+not)",
        rf"(?:{PERSON}|coming)\s+from\s+(?:poor|rich|working[\s-]?class)",
        rf"(?:immigrant|international|foreign)\s+{PERSON}?{GAP}{{0,40}}?"
        r"(?:can't|cannot|won't|will\s+not|struggle|lacks?|missing)",
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
