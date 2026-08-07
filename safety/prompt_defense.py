"""Prompt injection detection and defense."""

import re

import structlog

logger = structlog.get_logger()

# Shared injection patterns.
#
# ``sanitize()`` and ``is_injection_attempt()`` both build on these constants so
# the "clean" and "detect" sides of the defense cannot drift apart. That drift is
# the root cause of issue #64. Detection already knew ``\n---\n`` and ``\nSystem:``
# were dangerous, yet the sanitizer never acted on them.
SEPARATOR_PATTERN = r"\n\s*---+\s*\n"  # Separator line that can end the system prompt
ROLE_SWITCH_PATTERN = r"\n\s*(?:System|Human|Assistant)\s*:"  # Fake conversational turn
IGNORE_INSTRUCTION_PATTERN = r"\n\s*(?:Ignore|Forget|Disregard|Override)"  # Instruction override
TEMPLATE_PATTERN = r"{{.*?}}"  # Template injection
JINJA_PATTERN = r"{%.*?%}"  # Jinja-like injection
CODE_EXECUTION_PATTERN = r"(?:execute|run|eval)\s*\("  # Code execution attempts

# Pre-compiled forms of the newline-anchored patterns, used by ``sanitize()`` to
# neutralize the attacks that a plain character strip cannot reach.
_SEPARATOR_RE = re.compile(SEPARATOR_PATTERN)
_ROLE_SWITCH_RE = re.compile(ROLE_SWITCH_PATTERN, re.IGNORECASE)
_IGNORE_INSTRUCTION_RE = re.compile(IGNORE_INSTRUCTION_PATTERN, re.IGNORECASE)


class PromptDefense:
    """Defend against prompt injection attacks."""

    # Patterns indicating prompt injection attempts
    INJECTION_PATTERNS = [
        SEPARATOR_PATTERN,
        ROLE_SWITCH_PATTERN,
        TEMPLATE_PATTERN,
        JINJA_PATTERN,
        IGNORE_INSTRUCTION_PATTERN,
        CODE_EXECUTION_PATTERN,
    ]

    # Characters to strip from input
    DANGEROUS_CHARS = {
        "<": "",
        ">": "",
        "{": "",
        "}": "",
    }

    @staticmethod
    def _break_newline_anchor(match: re.Match[str]) -> str:
        """Neutralize a newline-anchored injection marker.

        The separator and role-switch attacks all rely on a leading line break to
        forge a prompt boundary. Turning every newline inside the matched marker
        into a space removes that boundary while preserving the visible words, so
        the marker can no longer read as the start of a new turn or the end of the
        system prompt.

        Args:
            match: A match of one of the newline-anchored injection patterns.

        Returns:
            The matched text with its internal newlines replaced by spaces.
        """
        return match.group(0).replace("\n", " ")

    @staticmethod
    def sanitize(text: str) -> str:
        """Sanitize user input to prevent injection.

        Removes template/markup delimiters and angle brackets, and neutralizes
        newline-based injection markers (separator lines such as ``\\n---\\n`` and
        role-switch markers such as ``\\nSystem:``) by breaking the line boundary
        they depend on. Ordinary paragraph newlines and legitimate content are
        preserved. The result no longer trips ``is_injection_attempt`` for the
        newline attacks this defends against.

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

        # Neutralize newline-anchored injection. Collapse separator lines to a
        # single space, then de-anchor role-switch and instruction-override
        # markers so a line break can no longer forge a prompt boundary. Order
        # matters here, because collapsing the separator first can expose a role
        # switch on the line that followed it (for example "\n---\nSystem:"),
        # which the next step then neutralizes.
        sanitized = _SEPARATOR_RE.sub(" ", sanitized)
        sanitized = _ROLE_SWITCH_RE.sub(PromptDefense._break_newline_anchor, sanitized)
        sanitized = _IGNORE_INSTRUCTION_RE.sub(PromptDefense._break_newline_anchor, sanitized)

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
