## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand
The `phone_us` pattern in `safety/pii_scrubber.py` starts with `\b`, a word-boundary
anchor, right before an optional `\(?`. A `\b` only matches between a word
character and a non-word character. When a phone number is preceded by a space
and starts with `(`, both sides of that position are non-word characters (space
and `(`), so `\b` never matches there and the whole pattern fails silently.

Expected: `scrub()` redacts `(555) 123-4567` to `[REDACTED]`, and `detect()`
reports a `phone_us` match for the same text.

Actual: confirmed with a direct regex test and with pytest — the dashed format
(`555-123-4567`) matches fine, but any parenthesized format doesn't match at
all, so `scrub()` leaves it untouched and `detect()` returns nothing for that
type. Ran the four named tests and all four fail:

```
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_us_phone_number_redaction
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_us_phone_formats
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_detect_phone_pii
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_phone_at_start_of_text
```

### Map
- `safety/pii_scrubber.py` — the `PII_PATTERNS["phone_us"]` regex is the only
  line that needs to change.
- `tests/unit/test_pii_scrubber.py` — no changes needed to make the four named
  tests pass, but I'll re-run the whole file to check for regressions,
  especially `test_international_phone_redaction` and
  `test_detect_multiple_pii_items` since they touch phone matching too.

### Plan
1. Replace the leading `\b` in `phone_us` with a boundary check that doesn't
   depend on `(` being a word character — either a negative lookbehind
   (`(?<![\w)])`) or restructure the pattern so the optional `(` is outside
   the boundary check.
2. Run `pytest tests/unit/test_pii_scrubber.py -v` and confirm the four
   originally-failing tests pass.
3. Run the full unit test file to check for regressions against email, SSN,
   and international phone patterns (they share the same `scrub()`/`detect()`
   loop and iterate patterns in dict order, so a looser phone regex could
   start swallowing characters another pattern expects).
4. Manually test a handful of extra formats not in the test file (e.g.
   `(555)123-4567` with no space, `555 123 4567` with spaces only) to sanity
   check the new pattern isn't overly narrow.
5. Run `make test-unit` to confirm the change is clean within the project's
   normal test workflow.

### Inputs & outputs
- Input: free-form text strings passed to `scrub()` or `detect()`, containing
  zero or more US phone numbers in dashed, dotted, parenthesized, or spaced
  formats.
- Output: `scrub()` returns the text with every matched phone number replaced
  by `[REDACTED]`; `detect()` returns a list of dicts with `type: "phone_us"`,
  the matched `value`, and accurate `start`/`end` character offsets.

### Risks & unknowns
- The `phone_intl` pattern (`\+[0-9]{1,3}[-.]?[0-9]{1,14}`) can overlap with
  `phone_us` on inputs like `+1 555 123 4567`. Loosening the `phone_us`
  boundary could change which pattern claims that match first, since
  `PII_PATTERNS` is a dict and `scrub()`/`detect()` iterate it in insertion
  order (email, phone_us, phone_intl, ssn, street_address).
- Need to confirm a negative lookbehind doesn't break matching at the very
  start of a string (`test_phone_at_start_of_text`), since there's no
  preceding character to look behind at index 0.
- `detect()` positions must stay accurate after the regex change — a wrong
  boundary could shift `start`/`end` by one character if the group structure
  changes.

### Edge cases
- Phone number at the very start of a string, with no preceding character.
- Phone number preceded by punctuation other than `(`, e.g. a colon or comma
  (`"Phone:(555) 123-4567"`).
- Parenthesized area code with no space before the next digits, e.g.
  `(555)123-4567`.
- Parenthesized number immediately followed by punctuation, e.g.
  `"(555) 123-4567."`.
- A string containing both a dashed and a parenthesized number, to confirm
  both get redacted, not just the first match.
