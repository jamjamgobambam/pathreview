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

    # Newline variants normalized to "\n" before the line-anchored substitutions
    # below run, so an attacker can't smuggle a role label past them with an
    # alternate separator (Windows, old Mac, or Unicode line/paragraph breaks).
    NEWLINE_VARIANTS = ("\r\n", "\r", "\u2028", "\u2029")

    # Line-anchored injection sequences that ``sanitize`` neutralizes. These
    # mirror the newline-based entries in ``INJECTION_PATTERNS`` so detection and
    # sanitization can't drift apart: anything ``is_injection_attempt`` flags via
    # a newline anchor, ``sanitize`` also defuses.
    _SEPARATOR_RE = re.compile(r"\n\s*-{3,}\s*(?=\n|$)")
    _ROLE_LABEL_RE = re.compile(r"\n\s*(System|Human|Assistant):", re.IGNORECASE)
    _IGNORE_RE = re.compile(r"\n\s*(Ignore|Forget|Disregard|Override)", re.IGNORECASE)

    @staticmethod
    def sanitize(text: str) -> str:
        r"""Sanitize untrusted user input before it enters an LLM prompt.

        In addition to stripping template delimiters and angle brackets, this
        neutralizes the newline-anchored sequences that ``is_injection_attempt``
        already flags, so attacker-controlled resume text can no longer visually
        terminate the system prompt or open a new conversational turn.

        Neutralization is deliberately surgical to avoid corrupting real resumes
        (blank lines, "Systems Engineer" titles, Markdown ``---`` rules survive):

        * Newline variants (``\r\n``, ``\r``, U+2028, U+2029) are normalized to
          ``\n`` first, so the patterns below can't be bypassed with an alternate
          line separator.
        * Standalone separator lines (``\n---\n``) collapse to a single space.
        * Role labels that open a new turn (``\nSystem:`` / ``Human:`` /
          ``Assistant:``) lose their leading newline and colon.
        * Explicit override lines (``\nIgnore`` / ``Forget`` / ``Disregard`` /
          ``Override``) lose their leading newline.

        Only newline/delimiter-based vectors are rewritten here; the
        ``execute(`` / ``run(`` / ``eval(`` vector is left to detection. The
        result is idempotent: ``sanitize(sanitize(x)) == sanitize(x)``.

        Args:
            text: User input text (untrusted).

        Returns:
            Sanitized text with the same readable content but injection
            delimiters and role labels neutralized.
        """
        sanitized = text

        # Normalize newline variants so alternate separators can't bypass the
        # line-anchored substitutions below.
        for variant in PromptDefense.NEWLINE_VARIANTS:
            sanitized = sanitized.replace(variant, "\n")

        # Strip template delimiters
        sanitized = sanitized.replace("{{", "").replace("}}", "")
        sanitized = sanitized.replace("{%", "").replace("%}", "")

        # Remove angle brackets
        sanitized = sanitized.replace("<", "").replace(">", "")

        # Neutralize newline-anchored injection sequences. Separator lines use a
        # lookahead so the trailing newline is preserved for the role-label pass
        # (e.g. "\n---\nSystem:" is defused by both substitutions in turn).
        sanitized = PromptDefense._SEPARATOR_RE.sub(" ", sanitized)
        sanitized = PromptDefense._ROLE_LABEL_RE.sub(lambda m: f" {m.group(1)} ", sanitized)
        sanitized = PromptDefense._IGNORE_RE.sub(lambda m: f" {m.group(1)}", sanitized)

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
