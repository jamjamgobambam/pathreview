"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts
    INJECTION_PATTERNS = [
        r"\n\s*---+\s*\n",  # Separator line
        r"\n[ \t]*(?:System|Human|Assistant)[ \t]*:",  # Role switching
        r"{{.*?}}",  # Template injection
        r"{%.*?%}",  # Jinja-like injection
        r"\n[ \t]*(?:Ignore|Forget|Disregard|Override)\b",  # Explicit instructions
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
        # Normalize line endings first so newline-based defenses behave the same
        # for LF, CRLF, and mixed input.
        sanitized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip template delimiters
        sanitized = sanitized.replace("{{", "").replace("}}", "")
        sanitized = sanitized.replace("{%", "").replace("%}", "")

        # Remove angle brackets
        sanitized = sanitized.replace("<", "").replace(">", "")

        # Break up line-based prompt boundaries without flattening legitimate
        # multiline content.
        sanitized = re.sub(r"(?m)^[ \t]*---+[ \t]*$", "", sanitized)
        sanitized = re.sub(
            r"(?m)^([ \t]*)(System|Human|Assistant)[ \t]*:[ \t]*",
            r"\1\2 - ",
            sanitized,
            flags=re.IGNORECASE,
        )
        sanitized = re.sub(
            r"(?m)^([ \t]*)(Ignore|Forget|Disregard|Override)\b[ \t]*",
            r"\1Instruction - \2: ",
            sanitized,
            flags=re.IGNORECASE,
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
