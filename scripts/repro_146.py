"""Reproduction script for issue #146.

Demonstrates that the *old* phone_us pattern (the one in the codebase before
commit 06230ad) fails to redact/detect space-separated parenthesized US phone
numbers like "(555) 123-4567", and that the *current* PIIScrubber.phone_us
pattern (safety/pii_scrubber.py) fixes it while still handling the other
documented formats.

Run with: python scripts/repro_146.py
"""

import re

from safety.pii_scrubber import PIIScrubber

OLD_PHONE_US_PATTERN = r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"

# (input, substring that must disappear once the number is correctly redacted)
SAMPLES = [
    ("Call me at (555) 123-4567 or 555-123-4567", "(555) 123-4567"),
    ("Contact: (555) 123-4567", "(555) 123-4567"),
    ("+1 555 123 4567 is my number", "555 123 4567"),
]


def redact(pattern: str, text: str) -> str:
    return re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)


if __name__ == "__main__":
    scrubber = PIIScrubber()
    current_pattern = scrubber.PII_PATTERNS["phone_us"]

    print("=== OLD pattern (pre-fix, from before commit 06230ad) ===")
    for text, needle in SAMPLES:
        scrubbed = redact(OLD_PHONE_US_PATTERN, text)
        print(f"  input:  {text}")
        print(f"  output: {scrubbed}")
        assert needle in scrubbed, (
            f"expected the OLD pattern to leave {needle!r} un-redacted -- "
            "this is the bug in issue #146"
        )
    print("  BUG CONFIRMED: space-separated parenthesized numbers slip through.\n")

    print("=== CURRENT pattern (safety/pii_scrubber.py) ===")
    for text, needle in SAMPLES:
        scrubbed = redact(current_pattern, text)
        print(f"  input:  {text}")
        print(f"  output: {scrubbed}")
        assert needle not in scrubbed
    print("  FIX CONFIRMED: all sample formats are now redacted.")
