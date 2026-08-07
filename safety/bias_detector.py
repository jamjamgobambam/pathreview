"""Bias detection in generated feedback."""

import re

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback."""

    # Broader phrases that dismiss educational backgrounds.
    DISMISSIVE_PATTERNS = [
        r"\b(?:bootcamp|coding\s+bootcamp|self[-\s]?taught|online\s+course)\b(?:\s+(?:education|training|background|experience))?\s+(?:is|are|was|were)?\s*(?:insufficient|inadequate|lacking|lacks|inferior|not\s+enough)",
        r"\b(?:bootcamp|self[-\s]?taught)\s+(?:graduates?|developers?|students?)\b.*\b(?:lack|missing|lack\s+of|missing\s+of)\b.*\b(?:rigor|fundamentals|proper\s+training|preparation)\b",
        r"\b(?:bootcamp|coding\s+bootcamp)\s+(?:graduates?|developers?|students?)\b.*\b(?:can't|cannot|won't|will\s+not|struggle\s+to|fail\s+to|doesn't|does\s+not)\b.*\b(?:write|build|ship|code|work|handle|perform|contribute|prepare)\b",
        r"\b(?:self[-\s]?taught|bootcamp)\s+(?:is|are|was|were)?\s*(?:not|never)\s+(?:equal|comparable|the\s+same)\s+to\s+(?:university|traditional|formal|college|degree)\b",
        r"\b(?:bootcamp|self[-\s]?taught|online\s+course)\b.*\b(?:doesn't|does\s+not)\s+prepare\s+(?:you|developers?|students?)\b",
    ]

    # Demographic assumptions (about age, background, identity).
    DEMOGRAPHIC_PATTERNS = [
        r"\b(?:young|old|aged|elderly)\s+(?:person|developer|programmer|candidate|engineer)s?\b.*\b(?:can't|cannot|won't|will\s+not|struggle\s+to|fail\s+to)\b",
        r"\b(?:person|developer|programmer|candidate|engineer)s?\s+from\s+(?:poor|rich|working[\s-]?class)\s+(?:background|backgrounds|families)?\b.*\b(?:can't|cannot|won't|will\s+not|struggle\s+to|fail\s+to)\b",
        r"\b(?:immigrant|international|foreign)\s+(?:developer|developers|programmer|programmers|candidate|candidates|engineer|engineers)\b.*\b(?:can't|cannot|won't|will\s+not|struggle|struggles|struggling|fail|fails|failing)\b",
        r"\b(?:age|gender|race|ethnicity|background)\s+(?:means|shows|proves)\b.*\b(?:inferior|worse|less\s+capable|less\s+qualified)\b",
    ]

    # Semantic context that indicates a bias claim even if the exact wording varies.
    BACKGROUND_TERMS = {
        "bootcamp",
        "coding bootcamp",
        "self taught",
        "self-taught",
        "online course",
        "online courses",
        "university",
        "college",
        "degree",
        "traditional education",
        "formal education",
        "young",
        "old",
        "aged",
        "elderly",
        "poor background",
        "rich background",
        "working class",
        "immigrant",
        "international",
        "foreign",
    }

    NEGATIVE_CLAIMS = {
        "can't",
        "cannot",
        "won't",
        "will not",
        "struggle",
        "struggles",
        "struggling",
        "fail",
        "fails",
        "failing",
        "lack",
        "lacks",
        "lacking",
        "missing",
        "inadequate",
        "insufficient",
        "inferior",
        "not equal",
        "not comparable",
        "doesn't prepare",
        "does not prepare",
        "doesn't have",
        "does not have",
        "less capable",
        "less qualified",
        "can't handle",
        "cannot handle",
        "won't handle",
        "can't write",
        "cannot write",
        "can't build",
        "cannot build",
    }

    COMPETENCE_TERMS = {
        "code",
        "coding",
        "developer",
        "developers",
        "programmer",
        "programmers",
        "engineering",
        "engineer",
        "systems",
        "production",
        "fundamentals",
        "training",
        "prepare",
        "learn",
        "communicate",
        "perform",
        "write",
        "build",
        "handle",
        "succeed",
    }

    _SENTENCE_SPLIT_RE = re.compile(r"[.!?\n]+")

    @staticmethod
    def detect_bias(text: str) -> tuple[bool, str]:
        """Detect biased language in feedback.

        Args:
            text: Feedback text

        Returns:
            Tuple of (is_biased, reason)
        """
        normalized_text = text.strip()
        if not normalized_text:
            return False, ""

        # Check for explicit dismissive language about education.
        for pattern in BiasDetector.DISMISSIVE_PATTERNS:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                reason = "Dismissive language about educational background"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        # Check for explicit demographic assumptions.
        for pattern in BiasDetector.DEMOGRAPHIC_PATTERNS:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                reason = "Demographic assumptions detected"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        # Fall back to a semantic heuristic that looks for a protected background
        # paired with a negative capability claim in the same sentence.
        semantic_result = BiasDetector._semantic_bias_detection(normalized_text)
        if semantic_result[0]:
            return semantic_result

        return False, ""

    @staticmethod
    def _semantic_bias_detection(text: str) -> tuple[bool, str]:
        """Detect bias from the relationship between background terms and negative claims."""
        sentences = [
            sentence.strip()
            for sentence in BiasDetector._SENTENCE_SPLIT_RE.split(text)
            if sentence.strip()
        ]
        if not sentences:
            sentences = [text]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            has_background_term = any(
                term in sentence_lower for term in BiasDetector.BACKGROUND_TERMS
            )
            if not has_background_term:
                continue

            has_negative_claim = any(
                term in sentence_lower for term in BiasDetector.NEGATIVE_CLAIMS
            )
            if not has_negative_claim:
                continue

            has_competence_term = any(
                term in sentence_lower for term in BiasDetector.COMPETENCE_TERMS
            )
            if has_competence_term:
                reason = "Semantically negative claim about educational or demographic background"
                logger.warning("bias_detected", reason=reason)
                return True, reason

        return False, ""
