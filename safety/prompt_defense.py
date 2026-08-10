"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    INJECTION_PATTERNS = [
        # Role switches & delimiters with flexible whitespace (Issue #64)
        r"\n[ \t]*(?:System|Human|Assistant)[ \t]*:",
        r"\n[ \t]*\[[ \t]*(?:SYSTEM|HUMAN|ASSISTANT)[ \t]*\]",
        r"\n[ \t]*---[ \t]*",
        r"\n[ \t]*===[ \t]*",
        # Original injection detection patterns
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
        """Sanitizes user input before placing it in prompt templates.

        Strips HTML and bracket formatting symbols and neutralizes multiline prompt
        injection control vectors (role switches and delimiter lines) regardless of
        leading whitespace or line-ending format.
        """
        if not text:
            return ""

        # Step 1: Strip bracket and HTML characters
        sanitized = re.sub(r"[{}<>]", "", text)

        # Step 2: Neutralize role switches (e.g., \n System : -> \n[sanitized-role]:)
        sanitized = re.sub(
            r"(\r?\n)[ \t]*(System|Human|Assistant)[ \t]*:",
            r"\1[sanitized-role]:",
            sanitized,
            flags=re.IGNORECASE,
        )

        # Step 3: Neutralize fake delimiter lines (e.g., \n --- -> \n[sanitized-delimiter])
        sanitized = re.sub(
            r"(\r?\n)[ \t]*(?:---|===)[ \t]*",
            r"\1[sanitized-delimiter]\1",
            sanitized,
        )

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
