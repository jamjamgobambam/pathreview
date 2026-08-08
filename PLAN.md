## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand

The PII scrubber successfully redacts common phone-number formats such as `555-123-4567`, but it does not recognize a parenthesized format such as `(555) 123-4567`. When the parenthesized number is passed to `scrub()`, it remains visible, and when it is passed to `detect()`, no phone-number detection is returned.

The root cause is the `phone_us` regular expression in `safety/pii_scrubber.py`. The pattern begins with a word boundary, which does not match correctly before an opening parenthesis. The separator portions of the expression also do not properly support spaces, including the space after the closing parenthesis.

Both `scrub()` and `detect()` use the same `phone_us` pattern, so correcting that pattern should fix both behaviors.

### Map

The main implementation and test locations are:

- `safety/pii_scrubber.py`
  - `PIIScrubber.PII_PATTERNS`
  - `PIIScrubber.scrub()`
  - `PIIScrubber.detect()`
- `tests/unit/test_pii_scrubber.py`
  - `test_us_phone_number_redaction`
  - `test_us_phone_formats`
  - `test_detect_phone_pii`
  - `test_phone_at_start_of_text`
  - `test_phone_at_end_of_text`

The expected production-code change is in `safety/pii_scrubber.py`. The existing tests already reproduce the bug, but I will review whether additional regression cases are needed in `tests/unit/test_pii_scrubber.py`.

### Plan

1. Update the `phone_us` regular expression in `safety/pii_scrubber.py` so that it can match an optional parenthesized area code without relying on a word boundary before `(`.
2. Allow the supported separators, including spaces, between the country code, area code, exchange code, and final four digits.
3. Run the focused phone-number tests and confirm that the four currently failing tests pass.
4. Verify that existing supported formats, including dashed and dotted phone numbers, continue to work.
5. Run the complete PII scrubber test file to check that the regex change does not break email, SSN, international-phone, or address redaction.

### Inputs & outputs

The input is text that may contain a US phone number, including formats such as:

- `555-123-4567`
- `(555) 123-4567`
- `555.123.4567`
- `+1 555 123 4567`

For `scrub()`, the expected output is the original text with the complete phone number replaced by `[REDACTED]`.

For `detect()`, the expected output is a detection entry containing the type `phone_us`, the matched phone-number value, and its start and end positions.

### Risks & unknowns

A regex that is too broad could incorrectly identify unrelated numeric text as a phone number. The change must support spaces and parentheses without matching malformed or incomplete numbers.

The `phone_us` and `phone_intl` patterns are both applied to the same text, so I need to check whether a number with a `+1` country code could be detected twice or partially matched.

I also need to confirm whether separators can be mixed and whether the project intends to support formats such as `555 123 4567` in addition to the formats already listed in the tests.

### Edge cases

The fix should handle:

- A parenthesized number in the middle of text
- A parenthesized number at the beginning of text
- A phone number at the end of text
- Dashed, dotted, and space-separated formats
- An optional `+1` US country code
- Punctuation immediately before or after a phone number
- Multiple phone numbers in the same text
- Incomplete or malformed phone numbers that should not be redacted