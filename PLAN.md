## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand
Root cause (two parts, found via testing): (1) the `phone_us` regex starts with
`\b`, which requires a word/non-word boundary — but `(` is a non-word char, so
when preceded by a space (also non-word), no boundary exists and the match
never starts. (2) `\)?[-.]?` after the area code doesn't include whitespace, so
even where the match starts, the space in "(555) 123" isn't consumed. Expected:
scrub() redacts and detect() flags parenthesized numbers like dashed ones.
Actual: they pass through completely untouched in both scrub() and detect().

### Map
- `safety/pii_scrubber.py` line 15 — the `phone_us` pattern needs its leading
  `\b` replaced with `(?<!\d)`, and `[-.\s]?` added after the optional closing
  paren
- `tests/unit/test_pii_scrubber.py` — 4 tests must pass:
  test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii,
  test_phone_at_start_of_text

### Plan
1. Replace the `phone_us` regex at line 15 with:
   `r"(?<!\d)(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.]?([0-9]{4})\b"`
2. Re-run test_us_phone_number_redaction and test_phone_at_start_of_text,
   confirm parenthesized format now redacts
3. Re-run test_detect_phone_pii, confirm detect() flags it (uses same pattern)
4. Re-run test_us_phone_formats fully — check whether "+1 555 123 4567"
   (space-separated, no dashes) also needs a separate fix, since that format
   uses spaces between all groups, not just after the parenthesis
5. Run the full test_pii_scrubber.py suite (all 25 tests) to confirm no
   regressions on the 2 currently-passing formats or other PII types

### Inputs & outputs
Input: free-text strings potentially containing US phone numbers in any
supported format. Output: scrub() returns text with phone numbers replaced by
[REDACTED]; detect() returns a list of PII matches with type and position.

### Risks & unknowns
- Changing `\b` to `(?<!\d)` is more permissive at the start — need to check it
  doesn't cause the pattern to match inside larger digit sequences (e.g. part
  of a longer ID number)
- Unclear whether "+1 555 123 4567" (all-space-separated) is in scope for this
  issue or needs a follow-up fix — test_us_phone_formats includes it in the
  same test, so it may surface as a new failure once the paren case is fixed
- Need to confirm detect() calls the same phone_us pattern as scrub() (looks
  likely from the shared PATTERNS dict, but worth verifying in the class body)

### Edge cases
- (555) 123-4567 (space after paren — reported case)
- (555)123-4567 (no space after paren)
- (555)-123-4567 (dash after paren)
- Parenthesized number at the very start of a string
- Parenthesized number immediately followed by punctuation, e.g. "(555) 123-4567."
- Multiple phone numbers of mixed formats in the same string