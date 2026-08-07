"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


# Reproduces #151: DISMISSIVE_PATTERNS and DEMOGRAPHIC_PATTERNS require
# near-exact phrase sequences and miss natural phrasings of the same bias.
# e.g. detect_bias("The candidate only attended a bootcamp, so this project
# lacks the rigor of a formal CS education") returns (False, "") instead of
# being flagged. Confirmed via `pytest tests/unit/test_bias_detector.py -v`:
# 9 related failures, including test_dismissive_bootcamp_language_detected
# and test_demographic_assumption_age_detected.
class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+is\s+(?:insufficient|inadequate|lacks)",
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?|education)\s+(?:lack|lacks|missing)\s+(?:rigor|fundamentals|proper\s+training)",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        r"(?:self-taught|bootcamp)(?:\s+developers?|\s+programmers?|\s+graduates?)?\s+(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:graduates?|developers?|programmers?)\s+(?:can't|cannot)\s+(?:write|handle)\s+(?:production\s+|enterprise\s+)?(?:code|systems)",
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:attendance|education|training)\s+means\s+(?:insufficient|inadequate|lacking|lacks)",
        r"(?:bootcamp)[^.!?]*(?:lacks|lacking)\s+(?:the\s+)?(?:rigor)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|developers?|programmers?)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:person\s+from|coming\s+from|developers?\s+from|programmers?\s+from)\s+(?:poor|rich|working[\s-]?class)",
        r"(?:immigrant|international|foreign)\s+developers?.*(?:can't|cannot|won't|struggle)",
        r"(?:their|his|her)\s+age[^.!?]*(?:can't|cannot|won't|will\s+not)",
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
