"""Bias detection in generated feedback."""

import re
from typing import TypedDict

import structlog

logger = structlog.get_logger()


# Maximum number of word-tokens allowed between a "subject" term and a
# "dismissive predicate" term for them to count as co-occurring in the same
# clause. Punctuation between them is allowed and does not count as a word.
_WINDOW = 8

# Sequence linking a subject to a predicate: any punctuation/whitespace, then up
# to _WINDOW intervening words, then the separator before the predicate.
_GAP = r"(?:\W+\w+){0," + str(_WINDOW) + r"}?\W+"

# Dismissive / negative predicates shared across every bias category. These are
# the "capability put-down" half of the signal — a subject term alone (or a
# subject next to *positive* wording) is never flagged.
_PREDICATES = [
    r"lacks?",
    r"missing",
    r"insufficient",
    r"inadequate",
    r"unqualified",
    r"(?:aren'?t|isn'?t)\s+(?:as\s+)?(?:capable|good|qualified|skilled|ready|prepared|suited)",
    r"not\s+(?:as\s+)?(?:capable|good|qualified|skilled|ready|prepared|suited|equal|comparable)",
    r"never\s+(?:equal|comparable|as\s+good)",
    r"(?:can'?t|cannot|won'?t|will\s+not)\s+"
    r"(?:be\s+able|cut\s+it|keep\s+up|handle|write|code|compete|succeed|communicate|afford|learn|understand)",
    r"don'?t\s+have\s+(?:the\s+)?(?:fundamentals|skills|experience|rigor|training|foundation|basics)",
    r"doesn'?t\s+(?:prepare|have|belong)",
    r"struggles?",
    r"struggling",
    r"less\s+(?:suited|capable|qualified)",
    r"too\s+demanding",
    r"hard\s+time",
    r"not\s+ready",
]


class _Category(TypedDict):
    reason: str
    subjects: list[str]


# Subject terms per bias category. Matching requires a subject AND a predicate
# from _PREDICATES within _WINDOW words of each other (in either order).
_CATEGORIES: dict[str, _Category] = {
    "education": {
        "reason": "Dismissive language about educational background",
        # Bare "bootcamp" is excluded when it modifies a work artifact
        # ("bootcamp project", "bootcamp repo") so praise/critique of the work
        # itself is not misread as bias about the person's background.
        "subjects": [
            r"bootcamp(?!\s+(?:project|projects|repo|repos|app|apps|assignment|assignments|code|portfolio))",
            r"coding\s+bootcamp",
            r"self[\s-]?taught",
            r"online\s+courses?",
            r"non[\s-]?traditional\s+background",
            r"(?:without|no)\s+(?:a\s+)?(?:cs\s+)?degree",
        ],
    },
    "age": {
        "reason": "Demographic assumptions detected",
        "subjects": [
            r"\byoung\b",
            r"\bold\b",
            r"\baged\b",
            r"\bage\b",
            r"older\s+(?:developer|programmer|worker)s?",
        ],
    },
    "origin": {
        "reason": "Demographic assumptions detected",
        "subjects": [
            r"immigrants?",
            r"international",
            r"foreign",
            r"(?:poor|rich|working[\s-]?class)\s+backgrounds?",
            r"from\s+(?:a\s+)?(?:poor|rich|working[\s-]?class)",
        ],
    },
    "gender": {
        "reason": "Demographic assumptions detected",
        "subjects": [
            r"\bwomen\b",
            r"\bwoman\b",
            r"female\s+(?:developer|programmer|engineer)s?",
        ],
    },
}

# Self-contained biased idioms that don't need a separate predicate nearby.
_DIRECT_PATTERNS = [
    (r"too\s+(?:old|young)\s+to\s+\w+", "Demographic assumptions detected"),
    (r"past\s+(?:your|their|his|her)\s+prime", "Demographic assumptions detected"),
]


def _compile_patterns() -> list[tuple[re.Pattern[str], str]]:
    """Build the compiled (pattern, reason) list once at import time."""
    predicate_alt = "(?:" + "|".join(_PREDICATES) + ")"
    compiled: list[tuple[re.Pattern[str], str]] = [
        (re.compile(pat, re.IGNORECASE), reason) for pat, reason in _DIRECT_PATTERNS
    ]
    for category in _CATEGORIES.values():
        subject_alt = "(?:" + "|".join(category["subjects"]) + ")"
        reason = category["reason"]
        # Match subject→predicate and predicate→subject within the window.
        compiled.append((re.compile(subject_alt + _GAP + predicate_alt, re.IGNORECASE), reason))
        compiled.append((re.compile(predicate_alt + _GAP + subject_alt, re.IGNORECASE), reason))
    return compiled


class BiasDetector:
    """Detect biased language in feedback.

    Flags text when a demographic/educational *subject* co-occurs with a
    *dismissive predicate* within a small word window, in either order. This
    catches common paraphrases (any subject x any predicate) that rigid
    full-sentence templates would miss, while leaving neutral/positive mentions
    untouched (a subject next to praise has no dismissive predicate to match).
    """

    _PATTERNS = _compile_patterns()

    @staticmethod
    def detect_bias(text: str) -> tuple[bool, str]:
        """Detect biased language in feedback.

        Args:
            text: Feedback text

        Returns:
            Tuple of (is_biased, reason)
        """
        for pattern, reason in BiasDetector._PATTERNS:
            if pattern.search(text):
                logger.warning("bias_detected", reason=reason)
                return True, reason

        return False, ""
