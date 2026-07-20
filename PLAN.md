## Solution plan

**Issue:** `pii_scrubber.py` test coverage doesn't include address formats — https://github.com/jamjamgobambam/pathreview/issues/73

### Understand

The PII scrubber is meant to redact home addresses from generated feedback, but
two related problems exist:

1. **Functional gap.** The `street_address` regex in `PII_PATTERNS`
   (`safety/pii_scrubber.py:18`) fails to match common address formats:
   - Numbered street names (`123 5th Avenue`, `123 42nd Street`) — the name
     portion `[A-Za-z\s]+` rejects digits.
   - Lettered house numbers (`221B Baker Street`) — `\d+` alone won't accept the
     trailing letter.
   - PO boxes (`PO Box 1234`) — there is no pattern for them at all.
2. **Test-coverage gap.** `test_address_variations`
   (`tests/unit/test_pii_scrubber.py:193`) calls `scrub()` in a loop but makes
   no assertions, so it passes vacuously and proves nothing.

- **Expected:** `scrub()` replaces these address formats with `[REDACTED]`, and
  `detect()` reports them; ordinary text is left untouched.
- **Actual:** the strings pass through unchanged and `detect()` returns `[]`,
  while the test suite still reports the address tests as passing.

### Map

- `safety/pii_scrubber.py` — the `PIIScrubber` class. Specifically the
  `PII_PATTERNS` dict (`street_address` entry), consumed by `scrub()` (via
  `re.sub`) and `detect()` (via `re.finditer`). No caller changes needed.
- `tests/unit/test_pii_scrubber.py` — the unit tests for the scrubber.

Files I expect to touch:
- `safety/pii_scrubber.py`
- `tests/unit/test_pii_scrubber.py`

### Plan

1. **Add failing tests first.** Replace the assertion-less
   `test_address_variations` with real assertions, and add tests for the leaking
   formats (numbered streets, lettered house numbers, PO boxes) plus negative
   cases. Confirm they fail against the current code (red).
2. **Broaden `street_address`.** Allow digits in the street-name words and an
   optional unit letter on the house number, while bounding the match so it
   doesn't over-redact ordinary prose (word-count limit + trailing word
   boundary).
3. **Add a `po_box` pattern** to `PII_PATTERNS` covering `PO Box`, `P.O. Box`,
   and case variants.
4. **Verify.** Run the pii_scrubber test file; confirm the new tests pass and no
   previously-passing tests regress. Re-run the reproduction snippet from
   JOURNAL.md to confirm the leaks are closed.
5. **Clean up & document.** Add a short comment on each regex explaining intent,
   and update PLAN.md / JOURNAL.md if understanding changed.

### Inputs & outputs

- **Input:** an arbitrary text string passed to `scrub(text)` / `detect(text)`
  (e.g. a chunk of generated feedback).
- **Output:**
  - `scrub()` returns the text with address substrings replaced by `[REDACTED]`.
  - `detect()` returns a list of dicts `{type, value, start, end}` including a
    `street_address` / `po_box` entry for each match.
  - No change to the public method signatures.

### Risks & unknowns

- **Over-redaction (false positives).** A looser regex could redact
  non-addresses like "I have 5 years experience" or "Room 101 upstairs". Mitigate
  with negative-case tests and a bounded name portion.
- **Catastrophic backtracking.** A poorly-formed pattern with nested quantifiers
  on long input could be slow. Keep quantifiers bounded (e.g. `{0,4}`) and test
  on a long string.
- **Ordering interactions.** Patterns are applied in sequence; a new pattern
  shouldn't collide with existing ones (email/phone/ssn). Verify with the full
  test file.
- **Unknown:** whether the graders expect ZIP-code redaction too. I'm treating
  ZIP as out of scope for now (high false-positive risk on any 5-digit number)
  and will note it as a possible follow-up rather than adding it blind.

### Edge cases

- Addresses embedded in a sentence: "I live at 456 Oak Avenue downtown".
- Address followed by a unit: "123 Main Street, Apt 4" (street portion redacted).
- Abbreviated suffix with a period: "10 Downing St.".
- Case variations: "po box 7", "P.O. BOX 12".
- Negative cases that must stay untouched: "Standard practices", "Version 2",
  "Room 101", "I have 5 years experience".
- Empty string / whitespace-only input (already handled; keep it working).
