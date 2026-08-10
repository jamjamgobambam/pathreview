"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts.
    #
    # Position-sensitive patterns are anchored to ``(?:^|\n)`` (start of the text
    # OR any line) rather than ``\n`` alone. Anchoring to ``\n`` only would miss a
    # first-line attack such as "Ignore all previous instructions" or "System: ..."
    # that is not preceded by a newline — the most common real-world case where a
    # user pastes an attack straight into an input field (see issue #71).
    INJECTION_PATTERNS = [
        # Separator line used to fake a new prompt section (start, middle, or end).
        r"(?:^|\n)\s*-{3,}\s*(?:\n|$)",
        # Role switching (System:/Human:/Assistant:) at the start of the text or a line.
        r"(?:^|\n)\s*(?:System|Human|Assistant)\s*:",
        # Template injection.
        r"{{.*?}}",
        # Jinja-like injection.
        r"{%.*?%}",
        # Explicit ignore/override command at the start of the text or a line.
        r"(?:^|\n)\s*(?:Ignore|Forget|Disregard|Override)\b",
        # Instruction-override phrasing anywhere, e.g. "please ignore all previous
        # instructions" or "disregard your system prompt".
        r"\b(?:ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}?"
        r"\b(?:instructions?|prompts?|rules?|context|directives?|guardrails?)\b",
        # Code execution attempts.
        r"(?:execute|run|eval)\s*\(",
    ]

    # Characters to strip from input
    DANGEROUS_CHARS = {
        "<": "",
        ">": "",
        "{": "",
        "}": "",
    }

    @staticmethod
    def sanitize(text: str) -> str:
        """Sanitize user input to prevent injection.

        Args:
            text: User input text

        Returns:
            Sanitized text
        """
        sanitized = text

        # Strip template delimiters
        sanitized = sanitized.replace("{{", "").replace("}}", "")
        sanitized = sanitized.replace("{%", "").replace("%}", "")

        # Remove angle brackets
        sanitized = sanitized.replace("<", "").replace(">", "")

        return sanitized

    @staticmethod
    def is_injection_attempt(text: str) -> bool:
        """Detect prompt injection attempt.

        Args:
            text: User input text

        Returns:
            True if injection attempt detected
        """
        for pattern in PromptDefense.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("injection_attempt_detected", pattern=pattern)
                return True

        return False
