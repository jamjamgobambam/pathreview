"""PII detection and scrubbing."""

import re

import structlog

logger = structlog.get_logger()


class PIIScrubber:
    """Detect and redact personally identifiable information."""

    # Regex patterns for common PII
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": (
            r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
            r"(?:\s?(?:ext\.?|x)\s?\d{1,5})?"
        ),
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": (
            r"\b\d+\s+(?:[A-Z][a-z]*\s+){0,3}"
            r"(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|"
            r"Drive|Dr\.?|Lane|Ln\.?|Court|Ct\.?|Circle|Cir\.?|Plaza|"
            r"Place|Pl\.?|Way|Parkway|Pkwy\.?|Point|Pt\.?|Pike|Run|"
            r"Summit|Terrace|Ter\.?|Trail|Trl\.?|Turnpike|View|Vista|"
            r"Village|Vlg\.?|Valley|Vly\.?)\b"
            r"(?:,?\s+(?:Apt\.?|Suite|Ste\.?|Unit|#)\s?\w+)?"
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
