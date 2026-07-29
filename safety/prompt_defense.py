"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts
    INJECTION_PATTERNS = [
        r"\n\s*---+\s*\n",  # Separator line
        r"\n\s*(?:System|Human|Assistant)\s*:",  # Role switching
        r"{{.*?}}",  # Template injection
        r"{%.*?%}",  # Jinja-like injection
        r"\n\s*(?:Ignore|Forget|Disregard|Override)",  # Explicit instructions to ignore
        r"(?:execute|run|eval)\s*\(",  # Code execution attempts
    ]

    # Newline boundary patterns neutralized by sanitize() (issue #64).
    # Detection stays broader (Ignore/Forget/eval); sanitize focuses on
    # prompt-boundary markers that can look like a new system turn.
    _SEPARATOR_PATTERN = re.compile(r"\n\s*---+\s*\n")
    _ROLE_SWITCH_PATTERN = re.compile(
        r"\n\s*(?:System|Human|Assistant)\s*:",
        re.IGNORECASE,
    )

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
            Sanitized text with template/angle-bracket markup removed and
            newline prompt-boundary markers (``---`` separators and
            System/Human/Assistant role labels) neutralized.
        """
        sanitized = text

        # Strip template delimiters
        sanitized = sanitized.replace("{{", "").replace("}}", "")
        sanitized = sanitized.replace("{%", "").replace("%}", "")

        # Remove angle brackets
        sanitized = sanitized.replace("<", "").replace(">", "")

        # Neutralize newline prompt boundaries (#64): collapse fake
        # separators, then strip role-switch labels while keeping the
        # remainder of the line so resume prose stays readable.
        sanitized = PromptDefense._SEPARATOR_PATTERN.sub("\n", sanitized)
        sanitized = PromptDefense._ROLE_SWITCH_PATTERN.sub("\n", sanitized)

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
