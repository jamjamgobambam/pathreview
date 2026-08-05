"""Bias detection in generated feedback."""

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    EDUCATIONAL_SUBJECTS = [
        "bootcamp",
        "coding bootcamp",
        "self-taught",
        "online course",
        "education",
        "training",
        "attendance",
        "graduates",
    ]

    DEMOGRAPHIC_SUBJECTS = [
        "young",
        "old",
        "aged",
        "immigrant",
        "international",
        "foreign",
        "poor",
        "rich",
        "working class",
        "working-class",
    ]

    NEGATIVE_PREDICATES = [
        "can't",
        "cannot",
        "won't",
        "will not",
        "doesn't",
        "does not",
        "struggle",
        "lack",
        "lacks",
        "missing",
        "insufficient",
        "inadequate",
        "not equal",
        "not comparable",
        "never comparable",
    ]

    @staticmethod
    def detect_bias(text: str) -> tuple[bool, str]:
        """Detect biased language in feedback.

        Args:
            text: Feedback text.

        Returns:
            Tuple of whether bias was detected and the corresponding reason.
        """
        normalized_text = text.lower()

        has_demographic_subject = any(
            subject in normalized_text for subject in BiasDetector.DEMOGRAPHIC_SUBJECTS
        )
        has_educational_subject = any(
            subject in normalized_text for subject in BiasDetector.EDUCATIONAL_SUBJECTS
        )
        has_negative_predicate = any(
            predicate in normalized_text for predicate in BiasDetector.NEGATIVE_PREDICATES
        )

        if has_demographic_subject and has_negative_predicate:
            reason = "Demographic assumptions detected"
            logger.warning("bias_detected", reason=reason)
            return True, reason

        if has_educational_subject and has_negative_predicate:
            reason = "Dismissive language about educational background"
            logger.warning("bias_detected", reason=reason)
            return True, reason

        return False, ""
