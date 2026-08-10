## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — #146
https://github.com/ascherj/pathreview/issues/146

### Understand
The PII scrubber (`safety/pii_scrubber.py`) redacts phone numbers via a `phone_us` regex:
`\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b`. After an optional closing
parenthesis, it only allows `-` or `.` as the separator — never a space. So formats like
`(555) 123-4567` or `+1 555 123 4567` never match at all.

Expected: any of these formats gets replaced with `[REDACTED]` (via `scrub()`) and reported by
`detect()`. 

Actual: they pass through completely untouched, leaking contact info. Confirmed
live: `re.search(pattern, "(555) 123-4567")` returns `None`.

### Map
- `safety/pii_scrubber.py` — `PIIScrubber.PII_PATTERNS["phone_us"]` is the regex to fix.
- `tests/unit/test_pii_scrubber.py` — existing phone tests to make pass, and where to add new
  parenthesized-format regression tests (`test_us_phone_number_redaction`,
  `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`).
- `PII_PATTERNS["phone_intl"]` and `["street_address"]` — adjacent patterns in the same dict;
  need to check the new phone regex doesn't start overlapping/double-matching with `phone_intl`.

### Plan
1. Update the `phone_us` regex so the separator after an optional closing paren (and between
   all digit groups) accepts a space in addition to `-`/`.`, e.g. `[-.\s]?` instead of `[-.]?`.
2. Manually verify the updated pattern against all known formats: `555-123-4567`,
   `(555) 123-4567`, `(555)123-4567`, `555.123.4567`, `+1 555 123 4567`, `+1 (555) 123-4567`.
3. Run `tests/unit/test_pii_scrubber.py` and fix any remaining failures caused by the phone
   pattern specifically (the `test_mixed_pii_and_text` failure is a separate, pre-existing
   `street_address` bug — see Risks below — not necessarily in scope here).
4. Add new unit tests covering parenthesized formats explicitly, per the issue's stated
   objective of preventing regressions.
5. Run `make check && make test-unit` for the full suite to confirm no unrelated regressions.

### Inputs & outputs
Input: arbitrary free-text strings (resume text, README content, profile fields) that may
contain zero or more phone numbers in any supported format, mixed with other text/PII.
Output: `scrub()` returns the same text with every matched phone number replaced by
`[REDACTED]`; `detect()` returns a list of `{type: "phone_us", value, start, end}` dicts for
each match, unchanged in shape from today.

### Risks & unknowns
- Loosening the separator to allow whitespace increases false-positive risk on unrelated
  digit runs (e.g. arbitrary "555 123 4567"-shaped non-phone numbers, dates, IDs) — needs a
  quick sanity check against the fixtures already in the test file.
- `phone_intl` pattern (`\+[0-9]{1,3}[-.]?[0-9]{1,14}`) can already match part of a
  `+1 555 123 4567` string; adding space-tolerance to `phone_us` may cause both patterns to
  match overlapping text, which is currently harmless (both just get redacted) but worth
  confirming doesn't double-count in `detect()`.
- Separately, `test_mixed_pii_and_text` fails today for an unrelated reason: `street_address`'s
  abbreviation list includes `Pl` (case-insensitive), which matches the tail of ordinary words
  like "applications". Not caused by, or necessarily fixed by, this issue — flagging so it isn't
  confused with the phone regression.

### Edge cases
- Phone number at the very start or end of a string (no surrounding whitespace/punctuation).
- Multiple phone numbers in one string, including mixed formats.
- Phone number adjacent to other PII (email, SSN, address) in the same text.
- Text with parentheses that aren't a phone number (e.g., "(see notes)") — must not be redacted.
- No phone number present at all — `scrub()`/`detect()` should be no-ops for that pattern.
