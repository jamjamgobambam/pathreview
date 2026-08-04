## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand
The `phone_us` regex in `safety/pii_scrubber.py` (`PII_PATTERNS["phone_us"]`)
uses `[-.]?` as the optional separator between the three digit groups. This
character class permits a dash or a dot but not a space. The parenthesized
format `(555) 123-4567` places a space immediately after the closing `)`,
so the regex fails to match starting at that point, and the entire pattern
returns no match for the string. Expected behavior: `scrub()` should redact
`(555) 123-4567` the same way it redacts `555-123-4567`, and `detect()`
should report it as a `phone_us` PII type. Actual behavior: both leave it
completely untouched, as if no PII pattern existed.

### Map
- `safety/pii_scrubber.py` — `PIIScrubber.PII_PATTERNS["phone_us"]` regex definition (the only file requiring a change)
- `tests/unit/test_pii_scrubber.py` — existing tests already cover the expected behavior (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`); no new tests should be needed, but I may add one for the `"+1 555 123 4567"` space-separated case if it isn't already independently verified

### Plan
1. Update the `phone_us` regex to include `\s` in both separator character classes: change `[-.]?` to `[-.\s]?` after the closing `\)?` and between the second and third digit groups
2. Re-run the regex directly with `re.search` against all four test formats (`555-123-4567`, `(555) 123-4567`, `555.123.4567`, `+1 555 123 4567`) to confirm matches before touching the class
3. Run `pytest tests/unit/test_pii_scrubber.py -k "phone"` and confirm all 6 tests pass (not just the 4 currently failing)
4. Run the full test suite (`pytest`) to confirm the change doesn't break unrelated PII types (email, SSN, street address) or the `phone_intl` pattern, since `phone_us` and `phone_intl` could both match international numbers
5. Manually test a few strings that should NOT match, to check for new false positives introduced by loosening the separator (e.g., plain 10-digit runs embedded in longer numbers, dates like "555 123 4567" is unlikely, but check ambiguous cases like partial SSNs or ID numbers with spaces)

### Inputs & outputs
**Input:** raw text strings passed to `scrub()` or `detect()`, potentially containing US phone numbers in any of: dashed, dotted, parenthesized, or space-separated format, with or without a leading `+1`.
**Output:** `scrub()` returns text with all matched formats replaced by `[REDACTED]`. `detect()` returns a list of dicts with `type: "phone_us"`, the matched value, and start/end character positions for each detected number.

### Risks & unknowns
- Adding `\s` to the separator class widens what counts as a "phone number," which risks false positives on other digit sequences separated by spaces (e.g., an SSN or a shipping tracking number with spaces instead of dashes) — worth checking `PII_PATTERNS["ssn"]` and other tests still pass after the change
- The `phone_intl` pattern (`\+[0-9]{1,3}[-.]?[0-9]{1,14}`) has the same separator gap and may also miss space-separated international numbers, but that's out of scope for issue #146 specifically — noting it here in case it should be a separate issue
- Need to confirm `\b` word boundaries still behave correctly once a space is allowed inside the match — `\s` is not a word character, so boundary behavior shouldn't change, but I'll verify with the start/end positions returned by `detect()`

### Edge cases
- Phone number at the very start of a string (already covered by `test_phone_at_start_of_text`)
- Phone number at the very end of a string (already covered by `test_phone_at_end_of_text`)
- Multiple phone numbers in the same text, mixing formats (e.g., the original issue's repro string with both a parenthesized and a dashed number)
- The `"+1 555 123 4567"` fully space-separated format with no parens or dashes at all
- Numbers with inconsistent separators, e.g. `(555)-123.4567` mixing styles in one number

## Update (Week 9)

**Scope note:** During implementation, the pre-commit hook blocked the commit
due to two pre-existing lint errors in `safety/pii_scrubber.py` (an unused
loop variable and a line-length violation on the unrelated `street_address`
pattern) that existed before this change touched the file. Per the "scope
grows" decision framework, I chose to fix these two lint-only issues
(no behavior change, verified byte-for-byte) rather than scope down further
or split into a separate PR, since they were blocking in the same file and
trivial to resolve. The `street_address` regex's actual behavioral bug
(unrelated false-positive match inside "applications") was left out of
scope and documented in the PR description instead, since fixing it would
expand this PR beyond issue #146.
