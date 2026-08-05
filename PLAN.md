## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand
The `phone_us` regex in `safety/pii_scrubber.py` matches dashed formats like
`555-123-4567` because it allows an optional dash/dot between digit groups.
However, after an optional closing parenthesis `\)?`, the pattern only allows
`[-.]?` (dash or dot) before the next group of digits — it does not account
for a space. Since `(555) 123-4567` has a space directly after the `)`, the
regex fails to match past the area code, so the number is never redacted and
never flagged by `detect()`. Expected behavior: both dashed and parenthesized
formats should be detected and redacted. Actual behavior: only dashed format
works.

### Map
- `safety/pii_scrubber.py` — contains the `PII_PATTERNS` dict and the
  `phone_us` regex that needs to be fixed
- `tests/unit/test_pii_scrubber.py` — contains the four failing tests named
  in the issue (`test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`) that will confirm
  the fix
- `test_repro.py` (my own reproduction script, root of fork) — not part of
  the fix, just used to confirm the bug locally

### Plan
1. Update the `phone_us` regex to allow an optional space (or dash/dot) both
   after the closing parenthesis and after the opening parenthesis, so
   `(555) 123-4567` is matched the same way `555-123-4567` is
2. Run the existing test suite (`tests/unit/test_pii_scrubber.py`) before
   changing anything, to get a baseline of what currently passes
3. Apply the regex fix and re-run the four named failing tests to confirm
   they now pass
4. Re-run the full test file to make sure the fix didn't break the
   already-passing dashed-format tests
5. Clean up `test_repro.py` (remove or repurpose) before opening the PR,
   since it was only for local verification

### Inputs & outputs
- **Input:** free-form text strings passed into `scrub()` and `detect()`,
  potentially containing US phone numbers in dashed, parenthesized, or plain
  digit formats
- **Output of `scrub()`:** the same text with any detected phone number
  (in any supported format) replaced with `[REDACTED]`
- **Output of `detect()`:** a list of dicts describing each detected PII
  match (type, value, start/end position) — parenthesized phone numbers
  should now appear in this list

### Risks & unknowns
- The `phone_us` pattern is shared logic used by both `scrub()` and
  `detect()` — any change needs to be verified against both, not just one
- Loosening the regex too much (e.g. making the space fully optional in the
  wrong spot) could cause it to accidentally match unrelated digit sequences
  elsewhere in text
- Need to double check the regex doesn't start colliding with the
  `phone_intl` pattern for numbers that include a `+` country code
- Not yet 100% sure if there are other "sometimes people write it this way"
  formats (e.g. `(555)123-4567` with no space at all) that should also be
  covered — I'll check the test file to see if additional formats are
  expected there

### Edge cases
- `(555) 123-4567` — space after parenthesis (the reported bug)
- `(555)123-4567` — no space after parenthesis
- `555-123-4567` — already-working dashed format (must not regress)
- `5551234567` — no separators at all
- A phone number appearing at the very start of a string (per
  `test_phone_at_start_of_text`)
- Text containing no phone number at all (should return unchanged / empty
  detection list)