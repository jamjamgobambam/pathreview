"""PII detection and scrubbing."""

import re

import structlog

logger = structlog.get_logger()


class PIIScrubber:
    """Detect and redact personally identifiable information."""

    # Regex patterns for common PII
    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        # Lookbehind instead of \b so a match can start at "(" — a word
        # boundary can never sit between a space and a paren, which left
        # the paren unredacted. \s in the separator class covers
        # "(555) 123-4567" and "+1 555 123 4567".
        "phone_us": (
            r"(?<!\w)(?:\+?1[-.\s]?)?" r"\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
        ),
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": (
            r"\b\d+\s+[A-Za-z\s]+"
            r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|"
            r"Court|Ct|Circle|Cir|Park|Pl|Plaza|Place|Drive|Dr|Way|Parkway|Pkwy|"
            r"Point|Pt|Pike|Run|Summit|Summit|Terrace|Ter|Trail|Trl|Tunnel|"
            r"Turnpike|View|Vista|Vlg|Village|Vly|Valley)\b"
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

        for pattern in self.PII_PATTERNS.values():
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

        logger.info("pii_detected", count=len(detected), types=len({d["type"] for d in detected}))

        return detected
