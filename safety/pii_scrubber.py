"""PII detection and scrubbing."""

import re

import structlog

logger = structlog.get_logger()

# Street suffixes the address pattern recognises, ordered longest-form first so
# the alternation prefers "Street" over "St" and "Parkway" over "Park".
# Public so tests can generate addresses from the same list the pattern uses.
STREET_SUFFIXES: tuple[str, ...] = (
    # fmt: off
    # Full words
    "Street", "Avenue", "Boulevard", "Drive", "Lane", "Court", "Circle",
    "Plaza", "Place", "Parkway", "Point", "Pike", "Road", "Run", "Summit",
    "Terrace", "Trail", "Tunnel", "Turnpike", "Village", "Valley", "Vista",
    "View", "Park", "Way",
    # Abbreviations
    "Ave", "Blvd", "Pkwy", "Cir", "Ter", "Trl", "Vlg", "Vly",
    "St", "Rd", "Dr", "Ln", "Ct", "Pl", "Pt",
    # fmt: on
)

# Patterns whose tokens are short enough that case-insensitive matching would
# fire inside ordinary words: lowercased, the two-letter street abbreviations
# "Dr"/"Pl"/"St" match inside "adr", "applications", "streetwise".
_CASE_SENSITIVE = frozenset({"street_address"})


def _compile(patterns: dict[str, str]) -> dict[str, re.Pattern[str]]:
    """Compile each pattern with the case sensitivity that pattern requires."""
    return {
        name: re.compile(pattern, 0 if name in _CASE_SENSITIVE else re.IGNORECASE)
        for name, pattern in patterns.items()
    }


class PIIScrubber:
    """Detect and redact personally identifiable information."""

    # Regex patterns for common PII.
    #
    # Separator classes are `[-.\s]` throughout: humans write phone numbers and
    # SSNs with spaces at least as often as with hyphens, and a pattern that
    # matches only part of a number is worse than one that misses it entirely --
    # it produces output that *looks* redacted while leaking the rest.
    #
    # `phone_intl` is ordered ahead of `phone_us` deliberately. Substitution is
    # sequential, so if `phone_us` ran first it would consume the national part
    # of "+2-000-000-0000" and leave the country code stranded outside the
    # redaction.
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        # +CC followed by two or more digit groups. Requiring two groups keeps
        # short numeric tokens like "+12" from being treated as phone numbers,
        # and consuming *every* group is what stops the subscriber number from
        # surviving a redaction of the country code.
        "phone_intl": r"\+\d{1,3}(?:[-.\s]?\d{1,4}){2,6}\b",
        # Optional trunk/country prefix, parenthesized or bare area code, then
        # 3+4 digits separated by any of -, ., space or nothing.
        #
        # The leading lookbehind rather than `\b` is load-bearing twice over: it
        # still refuses to start mid-way through a longer digit run, but unlike
        # `\b` it also permits a match to begin at "(" and to run straight from
        # an unseparated trunk prefix into the area code ("1000-000-0000").
        "phone_us": r"(?<![-.\d])(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        # Hyphen- or space-separated, and the separator must be consistent.
        "ssn": r"\b(?!000|666)\d{3}([- ])(?!00)\d{2}\1(?!0000)\d{4}\b",
        # House number, one to four capitalized name words, then a suffix. The
        # name words are required and must be capitalized: without that, a bare
        # digit followed by prose ("5 years...") matches on the suffix alone.
        "street_address": (
            r"\b\d+\s+(?:[A-Z][A-Za-z.]*\s+){1,4}" rf"(?:{'|'.join(STREET_SUFFIXES)})\b"
        ),
    }

    _COMPILED = _compile(PII_PATTERNS)

    def scrub(self, text: str) -> str:
        """Scrub PII from text.

        Args:
            text: Text to scrub

        Returns:
            Text with PII replaced by [REDACTED]
        """
        scrubbed = text

        for pattern in self._COMPILED.values():
            scrubbed = pattern.sub("[REDACTED]", scrubbed)

        return scrubbed

    def detect(self, text: str) -> list[dict]:
        """Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII with type, value, and position
        """
        detected = []

        for pii_type, pattern in self._COMPILED.items():
            for match in pattern.finditer(text):
                detected.append(
                    {
                        "type": pii_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        logger.info(
            "pii_detected",
            count=len(detected),
            types=len({d["type"] for d in detected}),
        )

        return detected
