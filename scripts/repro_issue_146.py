"""Reproduction script for issue #146.

PII scrubber fails to redact parenthesized US phone numbers.
https://github.com/ascherj/pathreview/issues/146

Run with the project venv active:

    source .venv/bin/activate
    python scripts/repro_issue_146.py

Observed output (2026-07-26, on this branch, BEFORE the fix):

    scrub(): Call me at (555) 123-4567 or [REDACTED]
    detect() on parens-only text: []
    detect() on dashed-only text: [{'type': 'phone_us', 'value': '555-123-4567', ...}]

The dashed number was redacted/detected correctly. The parenthesized number
was left completely untouched by scrub() and produced zero detections in
detect() when it was the only phone number present in the text.

Root cause: the `phone_us` pattern in safety/pii_scrubber.py already had
optional `\\(?` / `\\)?` groups around the area code, but the separator
allowed immediately after the closing `)` was restricted to `[-.]?` -- a
literal space was not in that character class. Since the conventional
parenthesized format is written as "(555) 123-4567" (space after the
paren), the match failed right after the closing paren and the whole
number was skipped.

Output AFTER the fix (widened separator class to `[-.\\s]?`, plus a
`(?<!\\w)` lookbehind replacing the leading `\\b` so a leading "(" or "+"
is included in the match):

    scrub(): Call me at [REDACTED] or [REDACTED]
    detect() on parens-only text: [{'type': 'phone_us', 'value': '(555) 123-4567', 'start': 11, 'end': 25}]
    detect() on dashed-only text: [{'type': 'phone_us', 'value': '555-123-4567', 'start': 11, 'end': 23}]

Known accepted trade-off: allowing whitespace as a separator (needed for
"(555) 123-4567" and "+1 555 123 4567") also means a bare 3-3-4 digit
sequence separated by spaces (e.g. "order 123 456 7890 units") is now
treated as a phone number. See PLAN.md Risks & Unknowns and
tests/unit/test_pii_scrubber.py::test_phone_us_space_separated_tradeoff.
"""

from safety.pii_scrubber import PIIScrubber

if __name__ == "__main__":
    scrubber = PIIScrubber()

    mixed_text = "Call me at (555) 123-4567 or 555-123-4567"
    parens_only = "Call me at (555) 123-4567"
    dashed_only = "Call me at 555-123-4567"

    print("scrub():", scrubber.scrub(mixed_text))
    print("detect() on parens-only text:", scrubber.detect(parens_only))
    print("detect() on dashed-only text:", scrubber.detect(dashed_only))
