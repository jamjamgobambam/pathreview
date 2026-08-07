## Solution plan

**Issue:** #146 — PII scrubber fails to redact parenthesized US phone numbers
https://github.com/[org]/pathreview/issues/146

### Understand
The PIIScrubber's phone_us regex in `safety/pii_scrubber.py` is supposed to
match US phone numbers in multiple formats, including ones with a
parenthesized area code like `(555) 123-4567`. The regex allows `-` or `.`
as the separator right after the closing parenthesis, but not a space.
Expected behavior: any phone number in `(XXX) XXX-XXXX` format, regardless
of the separator character after the parenthesis, should be detected and
redacted. Actual behavior: numbers with a space after `)` (the most common
real-world format) pass through completely untouched — no redaction at all.
This was confirmed with a regression test (see reproduction commit) and by
the 5 pre-existing failing tests in test_pii_scrubber.py, including
test_us_phone_number_redaction, test_us_phone_formats, and
test_detect_phone_pii.

### Map
- `safety/pii_scrubber.py` — contains the `phone_us` regex pattern that
  needs to change. This is the only file I expect to actually modify.
- `tests/unit/test_pii_scrubber.py` — where the regression test now lives,
  and where the existing failing tests should turn green once the fix lands.

### Plan
1. Locate the exact `phone_us` regex pattern in `pii_scrubber.py` and
   confirm the `[-.]?` separator group is the specific piece causing the bug.
2. Update the regex to also accept a space (and possibly no separator at
   all) after the closing parenthesis, without breaking the formats that
   already work (`555-123-4567`, `555.123.4567`, `+1 555 123 4567`).
3. Run the full test suite (`pytest tests/unit/test_pii_scrubber.py -v`)
   and confirm all previously-failing tests now pass, including my new
   regression test.
4. Manually test a handful of edge-case formats not explicitly covered by
   existing tests (see Edge cases below) to catch anything the test suite
   doesn't.
5. Confirm the unrelated street_address false-positive bug I noticed in
   Week 7 is untouched by this change, and note it as a separate,
   out-of-scope issue rather than trying to fix it here.

### Inputs & outputs
Input: raw text that may contain a US phone number in various formats,
including `(XXX) XXX-XXXX` with a space, hyphen, period, or nothing after
the closing parenthesis.
Output: `scrub()` should replace any matched phone number with
`[REDACTED]`; `detect()` should include it in its returned list with
type, value, start, and end position.

### Risks & unknowns
- Loosening the separator regex too much (e.g. making it match almost
  anything) could cause false positives on non-phone text that happens to
  contain a parenthesized number sequence.
- I don't yet know if this same `phone_us` pattern (or a copy of it) is
  reused anywhere else in the codebase — need to check for that before
  assuming a single-file fix is sufficient.
- The pre-commit hooks (mypy in particular) currently fail on this file
  for reasons unrelated to my change — 27 missing type-annotation errors
  across the whole test file. I'll need to decide whether to leave those
  alone (out of scope) or ask a mentor whether my PR is expected to fix them.

### Edge cases
- Extra or unusual whitespace after the parenthesis, e.g. `(555)  123-4567`
  (two spaces) or a tab character.
- No separator at all: `(555)123-4567`.
- Phone number with an extension, e.g. `(555) 123-4567 x1234`.
- Parenthesized number embedded mid-sentence vs. at the very start or end
  of the text (already partially covered by existing start/end tests).
- Multiple phone numbers in the same text, mixing formats (some with
  space, some with hyphen).