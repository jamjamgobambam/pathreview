"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Genuinely dismissive phrases about educational background
    DISMISSIVE_PATTERNS = [
        # "bootcamp/self-taught/online course education is insufficient/inadequate"
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+is\s+(?:insufficient|inadequate)",
        # "bootcamp education lacks fundamentals" (no "is" required)
        r"(?:bootcamp|self-taught|online\s+course)\s+(?:education|training)\s+lacks\s+(?:rigor|fundamentals)",
        # bootcamp/self-taught grads/devs/programmers lack rigor/fundamentals/training
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?)\s+(?:lack|missing)\s+(?:rigor|fundamentals|proper\s+training)",
        # bootcamp grads/devs/programmers can't write/handle/build/create X
        r"(?:bootcamp|self-taught)\s+(?:graduates?|developers?|programmers?)\s+(?:can't|cannot|won't|will\s+not)\s+(?:write|handle|build|create)\s+\S+(?:\s+\S+)?",
        # "bootcamp doesn't prepare you"
        r"(?:bootcamp|coding\s+bootcamp)\s+(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?)",
        # self-taught/bootcamp (devs) is/are not/never equal/comparable to formal ed
        r"(?:self-taught|bootcamp)(?:\s+(?:developers?|graduates?|programmers?))?\s+(?:is|are)\s+(?:not|never)\s+(?:equal|comparable)\s+to\s+(?:university|traditional|formal)",
        # "bootcamp attendance means inadequate training"
        r"(?:bootcamp|self-taught|online\s+course)\s+attendance\s+means\s+(?:inadequate|insufficient|lesser)\s+(?:training|education)",
    ]

    # Demographic assumptions (about age, background, identity)
    DEMOGRAPHIC_PATTERNS = [
        r"(?:young|old|aged)\s+(?:person|people|developer|developers|programmer|programmers)\s+(?:can't|cannot|won't|will\s+not)",
        r"(?:(?:person|people|developers?|programmers?)\s+from|coming\s+from)\s+(?:poor|rich|working[\s-]?class)",
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
        for pattern in BiasDetector.DISMISSIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                reason = "Dismissive language about educational background"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        for pattern in BiasDetector.DEMOGRAPHIC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                reason = "Demographic assumptions detected"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        return False, ""
