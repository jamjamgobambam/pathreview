Create PLAN.md at the repo root with this content, exactly as written, no edits:

## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers
https://github.com/ascherj/pathreview/issues/146

### Understand
The phone-number regex in `safety/pii_scrubber.py` is anchored with `\b`
(word boundary). `\b` only matches between a word character and a
non-word character. `(` is a non-word character, so when a phone number
starts with a parenthesized area code like `(555) 123-4567`, there's no
word-boundary transition at the point the pattern expects one, and the
match never triggers. Dashed formats like `555-123-4567` start with a
digit (a word character), so the boundary check passes fine there.
Confirmed locally: `test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, and `test_phone_at_start_of_text` all fail with
the exact behavior described in the issue, while `test_international_phone_redaction`
and `test_phone_at_end_of_text` pass, confirming the bug is specific to a
phone number opening with `(`, not the regex as a whole.

### Map
- `safety/pii_scrubber.py` — contains the `phone_us` regex pattern and the
  `PIIScrubber` class with `scrub()` and `detect()` methods. This is the
  only file I expect to change.
- `tests/unit/test_pii_scrubber.py` — contains the four failing tests
  confirmed above. I expect to make these pass without adding new tests,
  unless I find a gap they don't cover.

### Plan
1. Read the current `phone_us` regex pattern and confirm exactly how it's
   anchored and why `(` breaks it.
2. Update the pattern to accept an optional leading `(area code)` group
   alongside the existing dashed/dotted formats, without loosening the
   pattern enough to start matching non-phone-number digit sequences.
3. Run the four confirmed failing tests and verify they pass.
4. Run the full `test_pii_scrubber.py` suite to confirm the two currently
   passing tests (international, end-of-text) still pass, and nothing
   else in the suite regresses.
5. Manually re-run the reproduction snippet from Week 8 to confirm both
   phone formats are now redacted and detected.

### Inputs & outputs
Input: raw text strings passed to `scrub()` and `detect()`, potentially
containing phone numbers in various US formats.
Output: `scrub()` should return the text with all recognized phone
number formats replaced by `[REDACTED]`. `detect()` should return a
non-empty list of matches when any recognized format is present.

### Risks & unknowns
- Broadening the regex could cause false positives, matching
  non-phone-number parenthesized digit groups that happen to look
  similar. Need to check existing test fixtures for anything like this.
- Unsure yet whether `phone_us` is one regex or several patterns tried
  in sequence, need to read the actual file before finalizing the fix.
- `test_phone_at_start_of_text` failing alongside the others confirms
  the leading-parenthesis case needs to work both mid-sentence and at
  the very start of a string, so the fix has to handle both positions.

### Edge cases
- Phone number at the very start of a string (confirmed failing above).
- Phone number followed immediately by punctuation, e.g.
  `"(555) 123-4567."`
- Multiple phone numbers in one string, mixed formats.
- Parenthesized area code with no space before the local number, e.g.
  `(555)123-4567`.

Then append this Week 8 section to the end of JOURNAL.md, below the
existing Week 7 section. Do not touch or remove the Week 7 content:

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to be added after commit]

**Reproduction summary:**
Ran scrub() and detect() locally against a string containing both a dashed
and a parenthesized phone number. Confirmed the parenthesized format
passes through unredacted and detect() returns an empty list. Ran the
four named tests in test_pii_scrubber.py and confirmed all four fail
exactly as the issue describes, while two related phone tests
(international format, end-of-text position) pass, isolating the bug to
phone numbers that open with a parenthesis.

**PLAN.md link:** https://github.com/spicyneutrino/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm whether phone_us is a single regex or multiple patterns
before finalizing the exact fix approach in Week 9.
