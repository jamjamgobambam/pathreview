# Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers (#146)

## Understand

The PII scrubber correctly redacts several phone number formats, such as `555-123-4567`, but it fails to detect phone numbers where the area code is enclosed in parentheses, such as `(555) 123-4567`. Because these numbers are not detected, they remain visible instead of being replaced with `[REDACTED]`. A successful fix will ensure that parenthesized US phone numbers are detected and redacted while preserving support for the existing formats.

## Map

Files likely involved:

- `safety/pii_scrubber.py`
- `tests/unit/test_pii_scrubber.py`

Relevant code:

- `PII_PATTERNS["phone_us"]`
- `scrub()`
- `detect()`

## Plan

1. Examine the `phone_us` regular expression in `safety/pii_scrubber.py` to determine why parenthesized area codes are not matching.
2. Update the regular expression so it correctly matches phone numbers formatted as `(555) 123-4567`.
3. Run the existing unit tests in `tests/unit/test_pii_scrubber.py` to verify the updated regex passes the failing phone-number tests.
4. Verify that previously supported phone number formats (such as `555-123-4567`, `555.123.4567`, and `+1 555 123 4567`) continue to pass after the change.
5. Confirm that the `detect()` method correctly reports parenthesized phone numbers in addition to `scrub()` redacting them.

## Inputs & outputs

**Input:**

Text containing US phone numbers in different formats.

Examples:

- `(555) 123-4567`
- `555-123-4567`
- `555.123.4567`
- `+1 555 123 4567`

**Output:**

The scrubber should replace all supported phone number formats with `[REDACTED]`, and `detect()` should correctly identify them as `phone_us`.

## Risks & unknowns

- Updating the regular expression could unintentionally stop matching phone formats that currently work.
- The regex is shared by both `scrub()` and `detect()`, so changes affect both methods.
- Care must be taken to avoid matching invalid strings that are not phone numbers.

## Edge cases

- `(555)123-4567` (no space)
- `(555) 123-4567` (space after parenthesis)
- `555-123-4567`
- `555.123.4567`
- `+1 555 123 4567`
- Parenthesized phone number at the beginning of a sentence
- Parenthesized phone number at the end of a sentence