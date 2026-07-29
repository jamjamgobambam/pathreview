## Solution plan

**Issue:** #146 — PII scrubber fails to redact parenthesized US phone numbers
https://github.com/ascherj/pathreview/issues/146

### Understand
The `phone_us` regex in `safety/pii_scrubber.py` (line 15) is meant to catch
US phone numbers in multiple formats. It does include optional parenthesis
handling (`\(?` and `\)?`), so the intent to support "(555) 123-4567" is
already there, but it's incomplete. After the closing paren, the pattern only
allows a hyphen or period as a separator (`[-.]?`) before the next group of
digits. It does not allow a space. Since the standard parenthesized format
always has a space after the closing paren (e.g. "(555) 123-4567"), the
regex fails to bridge that gap and the whole match fails. Expected behavior:
detect() should flag this format as phone PII and scrub() should replace it
with [REDACTED], same as it already does for dashed and dotted formats.
Actual behavior: the number passes through both functions completely intact.

### Map
- `safety/pii_scrubber.py` — the file to change. Specifically the
  `phone_us` entry in the `PII_PATTERNS` dictionary (line 15).
- `tests/unit/test_pii_scrubber.py` — not modified, but this is what
  verifies the fix. Relevant tests: `test_us_phone_number_redaction`,
  `test_us_phone_formats`, `test_detect_phone_pii`,
  `test_phone_at_start_of_text`, and `test_mixed_pii_and_text`.

### Plan
1. Update the `phone_us` regex pattern so the separator after the optional
   closing parenthesis also accepts a space, not just hyphen/period
   (e.g. change `[-.]?` after `\)?` to `[-.\s]?` or similar).
2. Re-run `python -m pytest tests/unit/test_pii_scrubber.py -v` to confirm
   the four originally-failing phone tests now pass.
3. Manually test a few additional parenthesized variants in a Python shell
   (e.g. no space after parens, double space, tab) to check the fix isn't
   overly narrow.
4. Check `test_mixed_pii_and_text` separately - this test fails for an
   unrelated reason (partial match eating into "Python applications"),
   so confirm the phone fix doesn't affect it either way, and note it as
   a separate, pre-existing issue rather than something this fix needs to
   solve.
5. Commit the regex change with a clear message referencing issue #146.

### Inputs & outputs
**Input:** raw text strings potentially containing phone numbers in any
supported format (dashed, dotted, parenthesized, international).
**Output:** `scrub()` returns the text with matched phone numbers replaced
by `[REDACTED]`; `detect()` returns a list of dicts with type, value, start,
and end position for each match. After the fix, parenthesized numbers should
appear in both outputs the same way dashed numbers already do.

### Risks & unknowns
- Loosening the separator to include whitespace could make the regex too
  permissive and accidentally match sequences of digits that aren't phone
  numbers if they happen to be separated by spaces (e.g. arbitrary numeric
  data in a table). Need to test against `test_detect_no_false_positives`.
- The `test_mixed_pii_and_text` failure (words like "Python" getting
  partially redacted) is a separate bug in how patterns interact when run
  sequentially in `scrub()`. It's unclear yet whether it's caused by the
  `phone_us` pattern specifically or another pattern in the dict; this may
  need separate investigation and is not directly in scope for issue #146.
- Need to confirm the fix doesn't break the already-passing
  `test_phone_at_end_of_text` and `test_international_phone_redaction`
  tests, since all patterns run in the same loop in `scrub()`.

### Edge cases
- Phone number with no space after closing paren: "(555)123-4567"
- Phone number with extra space after closing paren: "(555)  123-4567"
- Parenthesized number at the very start or end of a string
- Parenthesized number immediately followed by punctuation (e.g. a period
  ending a sentence)
- Text containing a parenthetical aside that isn't a phone number at all,
  e.g. "(see attached)" followed by unrelated digits elsewhere in the text
