"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts.
    # Keep patterns anchored/specific to limit false positives on resume text.
    INJECTION_PATTERNS = [
        r"\n\s*---+\s*\n",  # Separator line
        r"(?:^|\n)\s*(?:System|Human|Assistant)\s*:",  # Role switching
        r"{{.*?}}",  # Template injection
        r"{%.*?%}",  # Jinja-like injection
        # Explicit override instructions (start of string or line)
        r"(?:^|\n)\s*(?:Ignore|Forget|Disregard|Override)\b",
        r"(?:execute|run|eval)\s*\(",  # Code execution attempts
        # Common jailbreak / red-team phrasings
        r"\bignore\s+all\s+previous\s+instructions\b",
        r"\bignore\s+previous\s+(?:rules|instructions|context)\b",
        r"\byou\s+are\s+now\s+DAN\b",
        r"\b(?:enter\s+)?developer\s+mode\b",
        r"\bdisable\s+all\s+safety\b",
        r"\bdecode\s+and\s+follow\b",
        # Encoded instruction payloads (Base64-looking blobs)
        r"(?i)(?:decode|base64).{0,40}[A-Za-z0-9+/]{16,}={0,2}",
        # XML / HTML-ish system role tags
        r"<\s*system\b[^>]*>",
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
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                logger.warning("injection_attempt_detected", pattern=pattern)
                return True

        return False
