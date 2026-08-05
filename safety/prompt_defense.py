"""Prompt injection detection and defense."""

import logging
import re

logger = logging.getLogger(__name__)


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

        # Strip newline injection patterns and role-switching markers
        for pattern in PromptDefense.INJECTION_PATTERNS:
            # FIX: Replace with a newline instead of a space
            sanitized = re.sub(pattern, "\n", sanitized, flags=re.IGNORECASE)

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
