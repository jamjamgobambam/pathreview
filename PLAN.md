## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers #146

### Understand
The phone_us regex uses `\b` before an optional `\(?`, but `\b` can't match
between two non-word characters (space then `(`), so the opening paren is
never actually captured. Separately, `[-.]?` only allows a dash or dot as a
separator — not a space — so "(555) 123-4567" can't bridge the gap between
")" and the next digit group. Result: scrub() leaves it unredacted, detect()
returns [].

### Map
- `safety/pii_scrubber.py` — PII_PATTERNS["phone_us"] regex
- `tests/unit/test_pii_scrubber.py` — existing/expected test coverage

### Plan
1. Update phone_us regex to allow whitespace as a valid separator character
2. Verify the leading `(` is actually consumed (not skipped due to \b)
3. Re-run the 4 named failing tests + full phone test suite
4. Manually test additional formats (leading/trailing text, mixed formats)
5. Check phone_intl and ssn patterns for the same boundary/separator issue

### Inputs & outputs
Input: raw text strings containing phone numbers in various formats.
Output: scrub() redacts all valid US phone formats; detect() reports them
with correct type/value/position.

### Risks & unknowns
- Loosening the separator class could cause false positives on unrelated
  digit sequences
- Need to confirm existing passing formats (dashed, dotted) don't regress
- Unsure whether to fix phone_intl/ssn in this PR or file a follow-up issue

### Edge cases
- Phone number at the very start or end of a string
- Multiple phone numbers, mixed formats, in one string
- Numbers with a leading "+1" country code plus parens