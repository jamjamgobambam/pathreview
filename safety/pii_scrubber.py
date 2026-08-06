"""PII detection and scrubbing."""

import re
import structlog

logger = structlog.get_logger()


class PIIScrubber:
    """Detect and redact personally identifiable information."""

    # Regex patterns for common PII
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        # US phone numbers. Separators may be a space, dot, or hyphen, so the
        # common parenthesized form "(555) 123-4567" (space after the area code)
        # is covered alongside "555-123-4567", "555.123.4567", "555 123 4567",
        # and an optional "+1"/"1" country code. Lookaround anchors let the
        # leading "(" be part of the match while still avoiding digits that are
        # glued to surrounding word characters. The separator class is space/
        # dot/hyphen (not \s) so a match never spans a line break.
        "phone_us": r"(?<!\w)(?:\+?1[ .-]?)?\(?([0-9]{3})\)?[ .-]?([0-9]{3})[ .-]?([0-9]{4})(?!\w)",
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Park|Pl|Plaza|Place|Drive|Dr|Way|Parkway|Pkwy|Point|Pt|Pike|Run|Summit|Summit|Terrace|Ter|Trail|Trl|Tunnel|Turnpike|View|Vista|Vlg|Village|Vly|Valley)",
    }

    def scrub(self, text: str) -> str:
        """Scrub PII from text.

        Args:
            text: Text to scrub

        Returns:
            Text with PII replaced by [REDACTED]
        """
        scrubbed = text

        for pii_type, pattern in self.PII_PATTERNS.items():
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
                detected.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })

        logger.info("pii_detected", count=len(detected), types=len(set(d["type"] for d in detected)))

        return detected
