"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts
    # You might see some injection patterns that have 2 backslashes,
    # this is because they are meant to be used in a raw string context
    # if you don't the REGEX replacement doesn't work as expected.
    INJECTION_PATTERNS = [
        r"\n\s*---+\s*\n",  # Separator line
        r"\\n---\\n",
        r"\n\s*(?:System|Human|Assistant):",  # Role switching
        r"\\n\s*(?:System|Human|Assistant):",  # Role switching
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

        # Remove Injection patterns
        for pattern in PromptDefense.INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

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
