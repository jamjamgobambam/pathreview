"""PII detection and scrubbing."""

import re

import structlog

logger = structlog.get_logger()


class PIIScrubber:
    """Detect and redact personally identifiable information."""

    # Regex patterns for common PII
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        # `(?<!\w)` (rather than a leading `\b`) lets the match include a
        # leading "(" or "+" even when preceded by whitespace/start-of-text,
        # where a `\b` assertion wouldn't fire before a non-word character.
        # Separators accept "-", "." or whitespace so parenthesized numbers
        # like "(555) 123-4567" and space-separated ones like
        # "+1 555 123 4567" are recognized alongside dashed/dotted formats.
        # Trade-off: any bare 3-3-4 digit sequence separated by spaces will
        # also match (e.g. "order 123 456 7890"), even if it isn't really a
        # phone number -- accepted here since over-redaction is the safer
        # failure mode for a PII scrubber.
        "phone_us": r"(?<!\w)(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": (
            r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
            r"Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Park|Pl|Plaza|Place|Drive|Dr|"
            r"Way|Parkway|Pkwy|Point|Pt|Pike|Run|Summit|Summit|Terrace|Ter|Trail|"
            r"Trl|Tunnel|Turnpike|View|Vista|Vlg|Village|Vly|Valley)"
        ),
    }

    def scrub(self, text: str) -> str:
        """Scrub PII from text.

        Args:
            text: Text to scrub

        Returns:
            Text with PII replaced by [REDACTED]
        """
        scrubbed = text

        for _pii_type, pattern in self.PII_PATTERNS.items():
            scrubbed = re.sub(pattern, "[REDACTED]", scrubbed, flags=re.IGNORECASE)

        return scrubbed

    def detect(self, text: str) -> list[dict]:
        """Detect PII in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected PII with type, value, and position
        """
        detected = []

        for pii_type, pattern in self.PII_PATTERNS.items():
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                detected.append(
                    {
                        "type": pii_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        pii_types = len(set(d["type"] for d in detected))
        logger.info("pii_detected", count=len(detected), types=pii_types)

        return detected
