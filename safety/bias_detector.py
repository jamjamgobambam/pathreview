"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background.
    # An education keyword (bootcamp / self-taught / online course) followed within a
    # bounded window by a negative predicate. This matches natural phrasings ("bootcamp
    # graduates can't write production code", "bootcamp education lacks fundamentals")
    # without requiring an exact word sequence, while positive/neutral mentions ("your
    # bootcamp background shows strong fundamentals") carry no negative predicate and so
    # stay unflagged.
    DISMISSIVE_PATTERNS = [
        r"(?:(?:coding\s+)?bootcamp|self-?taught|online\s+course)\b.{0,40}?\b"
        r"(?:can'?t|cannot|won'?t|will\s+not|lacks?|insufficient|inadequate"
        r"|not\s+(?:equal|comparable)|never\s+(?:equal|comparable)"
        r"|(?:isn'?t|aren'?t)\s+(?:equal|comparable))",
    ]

    # Demographic assumptions (about age, background, identity). Subjects allow both
    # singular and plural forms, and the background pattern accepts subjects beyond
    # "person from" (e.g. "developers from poor backgrounds"). The origin pattern uses a
    # bounded window rather than an unbounded ".*" to avoid catastrophic backtracking.
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:persons?|developers?|programmers?|engineers?)\s+(?:can'?t|cannot|won'?t|will\s+not)",
        r"(?:persons?|people|developers?|programmers?|engineers?|candidates?|those)\s+(?:from|coming\s+from)\s+(?:poor|rich|working[\s-]?class)",
        r"(?:immigrant|international|foreign)\s+developers?.{0,30}?(?:can'?t|cannot|won'?t|struggle)",
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
