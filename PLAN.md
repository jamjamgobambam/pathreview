## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand
The root cause is the `phone_us` pattern in `safety/pii_scrubber.py`: it does not reliably match the parenthesized US format `(555) 123-4567`, so `scrub()` leaves the number visible and `detect()` returns no phone PII. The expected behavior is that parenthesized, dashed, dotted, and space-separated US phone formats are all recognized consistently and redacted by the same pattern.

### Map
The main files involved are `safety/pii_scrubber.py` and `tests/unit/test_pii_scrubber.py`. The scrubber module owns the regex used by both `scrub()` and `detect()`, and the unit test file already contains the regression cases that currently fail. If the regex changes affect any broader safety behavior, I will also check the existing mixed-PII tests in that same test module.

### Plan
1. Update the US phone regex in `safety/pii_scrubber.py` so the parenthesized area-code form is matched without breaking the dashed and dotted formats.
2. Add or tighten regression tests in `tests/unit/test_pii_scrubber.py` for `(555) 123-4567` in both `scrub()` and `detect()` paths.
3. Run the focused pii scrubber test module to verify the phone cases pass and that unrelated PII cases still behave as expected.
4. If the regex change introduces a false positive or a mixed-PII regression, adjust the pattern or tests before widening the fix.

### Inputs & outputs
The input is free-form text that may contain a US phone number in multiple common formats. The fix should output the same text with phone numbers replaced by `[REDACTED]`, and `detect()` should emit a phone detection record with correct type and character positions.

### Risks & unknowns
A too-loose regex could redact version numbers, grouped digits, or other non-phone strings in `safety/pii_scrubber.py`. The mixed-content tests in `tests/unit/test_pii_scrubber.py` also show that phone redaction can interact with nearby text, so I need to watch for regressions where surrounding words are accidentally swallowed or partially redacted. I am also unsure whether the current phone pattern should be extended to support additional whitespace combinations beyond the specific parenthesized case, so I will keep the change as small as possible.

### Edge cases
Handle phones at the start or end of text, inside surrounding punctuation, and in mixed paragraphs with email or SSN content. Preserve existing behavior for already-supported formats like `555-123-4567`, `555.123.4567`, and `+1 555 123 4567`. Avoid redacting ordinary numeric strings, version numbers, or text that only looks phone-like at a glance.
