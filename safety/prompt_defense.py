"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts
    INJECTION_PATTERNS = [
        r"\n\s*---+\s*\n",  # Separator line
        r"\n\s*(?:System|Human|Assistant):",  # Role switching
        r"{{.*?}}",  # Template injection
        r"{%.*?%}",  # Jinja-like injection
        r"\n\s*(?:Ignore|Forget|Disregard|Override)",  # Explicit instructions to ignore
        r"(?:execute|run|eval)\s*\(",  # Code execution attempts
    ]

    # Characters to strip from input
    DANGEROUS_CHARS = {
        "<": "",
        ">": "",
        "{": "",
        "}": "",
    }

    # Newline-based injection patterns that sanitize() must strip.
    # Kept separate from INJECTION_PATTERNS so we don't remove code-execution
    # patterns like execute(...)/eval(...), which is out of scope for issue #64
    # and risks stripping legitimate technical resume content (e.g. "eval()").
    NEWLINE_INJECTION_PATTERNS = [
        r"\n\s*---+\s*\n",  # Separator line
        r"\n\s*(?:System|Human|Assistant):",  # Role switching
        r"\n\s*(?:Ignore|Forget|Disregard|Override)",  # Explicit ignore instructions
    ]

    @staticmethod
    def sanitize(text: str) -> str:
        """Sanitize user input to prevent injection.

        Args:
            text: User input text

        Returns:
            Sanitized text
        """
        sanitized = text

        # Remove newline-based injection patterns (issue #64). These are
        # already detected by is_injection_attempt() via INJECTION_PATTERNS,
        # but were never actually being stripped here.
        for pattern in PromptDefense.NEWLINE_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, " ", sanitized, flags=re.IGNORECASE)

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
