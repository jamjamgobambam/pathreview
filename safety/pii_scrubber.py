"""PII detection and scrubbing."""

import re

import structlog

logger = structlog.get_logger()


class PIIScrubber:
    """Detect and redact personally identifiable information."""

    # Regex patterns for common PII
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        # House number (with an optional unit letter, e.g. "221B") followed by
        # 1-4 street-name words (digits allowed so "5th"/"42nd" match) and a
        # street-type suffix. The trailing \b prevents the suffix from matching
        # inside a longer word (e.g. "Pl" inside "applications"); \.? absorbs an
        # abbreviated suffix's period ("St.").
        "street_address": r"\b\d+[A-Za-z]?\s+(?:[A-Za-z0-9]+\s+){1,4}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Plaza|Place|Pl|Way|Parkway|Pkwy|Point|Pt|Pike|Terrace|Ter|Trail|Trl|Turnpike|Village|Valley)\b\.?",
        # PO boxes: "PO Box 1234", "P.O. Box 1234", and case variants.
        "po_box": r"\bP\.?\s?O\.?\s+Box\s+\d+",
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
                detected.append(
                    {
                        "type": pii_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        logger.info(
            "pii_detected", count=len(detected), types=len(set(d["type"] for d in detected))
        )

        return detected
