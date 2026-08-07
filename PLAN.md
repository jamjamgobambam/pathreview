## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand
The phone_us regex in safety/pii_scrubber.py is:
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
After the optional closing parenthesis, it only allows a dash or dot before
the next group of digits — never a space. So "(555) 123-4567" breaks right
after the ")", since a real closing paren is always followed by a space,
not a dash/dot. Dash and dot formats work fine; only the parenthesized
format is broken. Expected: all four formats in test_us_phone_formats
should redact identically.

### Map
- `safety/pii_scrubber.py`, line 15 — the `phone_us` regex constant used by
  both `scrub()` and `detect()` (single shared pattern, confirmed by
  grep — not two separate copies, so one fix covers both methods)
- `tests/unit/test_pii_scrubber.py` — defines the four target tests, plus
  `test_mixed_pii_and_text`, which fails for an unrelated pre-existing
  overmatch bug (see Risks)

### Plan
1. Update the `phone_us` pattern to allow a space (in addition to dash/dot)
   as the separator right after the optional closing parenthesis:
   `\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.]?([0-9]{4})\b`
2. Run `test_us_phone_number_redaction` and `test_us_phone_formats` to
   confirm all four listed formats now redact correctly in scrub()
3. Run `test_detect_phone_pii` to confirm detect() picks up the same fix
   (it shares the same regex, so this should pass without a separate change)
4. Run `test_phone_at_start_of_text` to confirm the fix also works when the
   number is the first thing in the string
5. Re-run the full test file and confirm test_mixed_pii_and_text's failure
   is unchanged by my fix (i.e. it's a pre-existing, unrelated bug, not
   something my change makes worse)

### Inputs & outputs
- Input: free-text strings passed to scrub() and detect()
- Output: scrub() replaces matched phone numbers with [REDACTED]; detect()
  returns PII match objects. After the fix, (555) 123-4567 is treated
  identically to 555-123-4567 and 555.123.4567 in both methods

### Risks & unknowns
- Adding \s to the separator class could allow a stray space elsewhere in
  text to be swept into a false-positive phone match — need to check
  test_detect_no_false_positives still passes after the change
- test_mixed_pii_and_text already fails independently of this bug (it
  over-redacts "5 years developing Python appl..." down to a single
  [REDACTED]). Confirmed via grep this isn't caused by phone_us — it's a
  separate pattern or overlap issue. Out of scope for #146; I'll leave a
  note in JOURNAL.md rather than fix it here.

### Edge cases
1. Parenthesized number at the very start of a string with no leading
   space: "(555) 123-4567 is my phone number." (test_phone_at_start_of_text)
2. Dashed and parenthesized numbers together in the same string, to
   confirm the updated pattern doesn't break the dash format while fixing
   the parenthesized one
