## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand
The `phone_us` regex in `safety/pii_scrubber.py` used inconsistent separator
groups between the three digit groups of a phone number. The gap after the
optional area-code parenthesis allowed a space, dash, or dot (`[-.\s]?`), but
the gap before the final four digits only allowed a dash or dot (`[-.]?`),
with no space option. As a result, formats like `(555) 123-4567` and
`+1 555 123 4567` — both of which rely on a space separator somewhere in
the number — were never matched. Expected behavior: any common US phone
format (dashed, dotted, parenthesized, spaced, or a mix) should be detected
and redacted. Actual behavior (before fix): only fully dash/dot-separated
numbers like `555-123-4567` were caught; anything with a space passed
through `scrub()` unredacted and was invisible to `detect()`.

### Map
- `safety/pii_scrubber.py` — contains the `PII_PATTERNS` dict and the
  `phone_us` regex that needed correction. This is the only file changed
  for the core fix.
- `tests/unit/test_pii_scrubber.py` — existing test file with the four
  tests named in the issue (`test_us_phone_number_redaction`,
  `test_us_phone_formats`, `test_detect_phone_pii`,
  `test_phone_at_start_of_text`) that define what "fixed" means. No test
  changes were needed since the existing tests already covered the bug.

### Plan
1. Reproduce the bug locally by running the existing test suite and
   confirming which tests failed and why (`test_us_phone_formats`,
   later also `test_mixed_pii_and_text`, though the latter is unrelated).
2. Isolate the root cause by manually tracing the regex against each
   failing input format to find exactly which separator group was
   too strict.
3. Update the `phone_us` pattern so all three separator positions
   (after country code, after area code, before final four digits)
   consistently allow space, dash, dot, or nothing.
4. Re-run the full unit test suite to confirm the four named tests pass
   without breaking any previously-passing tests.
5. Document the reproduction and root cause directly in the code (comment
   above the regex) and in JOURNAL.md, then commit and push.

### Inputs & outputs
**Input:** raw text strings potentially containing US phone numbers in
various formats (dashed, dotted, parenthesized, spaced, or combinations),
passed to `PIIScrubber.scrub()` or `PIIScrubber.detect()`.
**Output:** `scrub()` returns the text with all matched phone numbers
replaced by `[REDACTED]`; `detect()` returns a list of dicts identifying
each phone number's type, value, and position in the text. After the fix,
both methods correctly catch all four format variants named in the issue.

### Risks & unknowns
- Loosening the separator groups too much could cause false positives —
  e.g., accidentally matching a run of digits that isn't actually a phone
  number (like a long ID or timestamp embedded in text). This needs to be
  watched for in `test_detect_no_false_positives`.
- The `phone_intl` pattern is separate and wasn't touched, but there could
  be overlap between `phone_us` and `phone_intl` matching the same
  substring differently — worth double-checking if new international test
  cases are added later.
- A separate, pre-existing bug in the `street_address` pattern (unrelated
  to this issue) causes `test_mixed_pii_and_text` to fail because "Pl" in
  "applications" gets matched as an address suffix. This is out of scope
  for issue #146 and should not be fixed as part of this PR, but is noted
  here in case it causes confusion during review.

### Edge cases
- Phone number at the very start or end of a string (already covered by
  `test_phone_at_start_of_text` / `test_phone_at_end_of_text`).
- Phone number immediately adjacent to other digits (e.g. part of a longer
  numeric ID) should NOT be falsely matched — handled by the `(?<!\d)` /
  `(?!\d)` lookaround boundaries.
- Numbers with a leading `+1` country code combined with spaces, e.g.
  `+1 555 123 4567`, must be matched as a single phone number, not broken
  into fragments.
- Multiple different phone formats appearing in the same text block
  should all be redacted independently (covered by
  `test_multiple_emails_redacted`-style multi-match tests).
