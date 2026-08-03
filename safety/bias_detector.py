"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback.

    Matching strategy: split text into clauses and check each clause for
    two independent things -- (1) a protected/dismissed category term
    (educational background, age, or socioeconomic/national background)
    and (2) a dismissive or negative-capability framing. Both must appear
    in the same clause for a match.
    """

    EDUCATION_TERMS = r"(?:bootcamp|self-taught|online\s+course)"
    ROLE_TERMS = r"(?:developers?|programmers?|engineers?|graduates?|persons?|people)"
    AGE_TERMS = r"(?:young|old|aged)"
    BACKGROUND_TERMS = r"(?:immigrant|international|foreign|working[\s-]?class|poor|rich)"

    CATEGORY_PATTERN = re.compile(
        rf"(?:{EDUCATION_TERMS})"
        rf"|(?:{AGE_TERMS})\s+(?:{ROLE_TERMS})"
        rf"|(?:{BACKGROUND_TERMS})",
        re.IGNORECASE,
    )

    NEGATIVE_PATTERN = re.compile(
        r"can't|cannot|won't|will\s+not|struggle"
        r"|lacks?|missing"
        r"|inadequate|insufficient"
        r"|(?:not|never)\s+(?:equal|comparable)\s+to"
        r"|means\s+inadequate"
        r"|doesn't\s+prepare|does\s+not\s+prepare",
        re.IGNORECASE,
    )

    @staticmethod
    def _split_clauses(text: str) -> list[str]:
        """Split text into clauses so category + negative terms must be local."""
        return re.split(r"[.;]|\s+and\s+", text)

    @staticmethod
    def detect_bias(text: str) -> tuple[bool, str]:
        """Detect biased language in feedback.

        Args:
            text: Feedback text

        Returns:
            Tuple of (is_biased, reason)
        """
        if not text or not text.strip():
            return False, ""

        for clause in BiasDetector._split_clauses(text):
            has_category = BiasDetector.CATEGORY_PATTERN.search(clause)
            has_negative = BiasDetector.NEGATIVE_PATTERN.search(clause)

            if has_category and has_negative:
                if re.search(BiasDetector.EDUCATION_TERMS, clause, re.IGNORECASE):
                    reason = "Dismissive language about educational background"
                else:
                    reason = "Demographic assumptions detected"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        return False, ""
