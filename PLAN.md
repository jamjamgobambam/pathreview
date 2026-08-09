## Solution plan

**Issue:** #146 — PII scrubber fails to redact parenthesized US phone numbers

### Understand
The `phone_us` regex pattern in `safety/pii_scrubber.py` (line 15) is used by both
`scrub()` and `detect()` to find US phone numbers. It correctly matches dashed and
dotted formats like `555-123-4567` or `555.123.4567`, but fails on the parenthesized
format `(555) 123-4567`.

The root cause is in the separator character class. The pattern uses `[-.]?` immediately
after the optional closing parenthesis `\)?` — this class only allows a dash or a dot,
not whitespace. Since `(555) 123-4567` has a space after the `)`, the regex cannot
continue matching past that point, and the entire match fails.

As a result:
- `scrub()` leaves the number completely unredacted in the output.
- `detect()` returns an empty list when a parenthesized number is the only PII present
  — a false negative, which is the more serious half of the bug, since it means the
  scrubber reports "no PII found" when PII is actually present.

**Root cause:** The `phone_us` regex separator class `[-.]?` does not include `\s`,
so it cannot match the space that appears after the closing parenthesis in `(555) 123-4567`.

### Map
Files touched:
- `safety/pii_scrubber.py` — the `phone_us` pattern in `PII_PATTERNS` (line 15).
  This is the only production code change needed.
- `tests/unit/test_pii_scrubber.py` — reproduction tests and edge-case tests added.
- No other files needed changes — `PIIScrubber` is used elsewhere in the app, but
  the interface and behavior of all other PII types are unaffected.

### Plan
1. ✅ Confirm the exact current regex and reproduce the bug — committed failing
   tests confirming both `detect()` returns `[]` and `scrub()` leaves the number
   unredacted.
2. ✅ Came up with an initial working fix — extended all three separator slots from
   `[-.]?` to `[-.\s]?` and replaced the leading `\b` with `(?<!\w)` for reliable
   boundary matching next to parentheses:
   ```python
   r"(?<!\w)(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})(?!\w)"
   ```
3. ✅ Optimized the fix further — removed unused capture groups since `scrub()` uses
   a fixed replacement string and `detect()` reads the whole match. Final pattern:
   ```python
   r"(?<!\w)(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
   ```
4. ✅ Ran reproduction tests — both `test_paren_phone_detect_reproduces_bug` and
   `test_paren_phone_scrub_reproduces_bug` now pass.
5. ✅ Ran full test file — 36 passed, 1 failed. The single failure
   (`test_mixed_pii_and_text`) is a pre-existing unrelated bug in the
   `street_address` pattern, not introduced by this fix.
6. ✅ Added 3 edge-case tests (country code + parens, multiple numbers in one string,
   malformed 2-digit area code negative case). Remaining edge-case tests to be added
   before final PR merge (trailing punctuation, position accuracy, inside quotes,
   all-spaces separator, SSN-not-matched-as-phone).
7. ✅ Ran `make check` — fixed 2 trailing whitespace issues in test file. Confirmed
   4 remaining ruff errors are all pre-existing in untouched lines of
   `safety/pii_scrubber.py`.
8. ✅ Ran `make test-unit` — 391 passed, 49 failed. All 49 failures are pre-existing
   across unrelated modules. Zero new failures introduced.
9. ⬜ Address draft PR review feedback.
10. ⬜ Add remaining edge-case tests before final merge.
11. ⬜ Record Loom walkthrough video.
12. ⬜ Update `JOURNAL.md` with final Week 9 summary.

### Inputs & outputs
**Pattern I changed:** `PII_PATTERNS["phone_us"]` in `safety/pii_scrubber.py`

**Before (buggy):**
```python
r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
```

**After (fixed + optimized):**
```python
r"(?<!\w)(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
```

**Existing happy path (unaffected):**
- Input: `"Call me at 555-123-4567"` → `scrub()` returns `"Call me at [REDACTED]"`

**Fixed behavior:**
- Input: `"Call me at (324) 901-1234"`
- Before: `scrub()` returns text unchanged; `detect()` returns `[]`
- After: `scrub()` returns `"Call me at [REDACTED]"`;
  `detect()` returns one entry with `"type": "phone_us"`

### Risks & unknowns
1. ✅ **Resolved — overly permissive whitespace matching.** Confirmed `\s` does not
   cause false positives in mixed-content tests or across scattered digit sequences.
   All existing tests pass with the updated pattern.
2. ✅ **Resolved — boundary anchor interaction.** Switching `\b` to `(?<!\w)` at the
   start was confirmed safe — `test_phone_at_start_of_text` and
   `test_phone_at_end_of_text` both pass. The trailing `\b` was retained since the
   pattern always ends on a digit, where it behaves predictably.
3. ⚠️ **Pre-existing unrelated bug noted.** While running the full suite,
   `test_mixed_pii_and_text` fails independently — the `street_address` pattern
   partially matches "Pl" inside "applications", producing "[REDACTED]ications".
   This is out of scope for #146 and was present before this fix. May be worth
   filing as a separate issue.

### Edge cases verified
- ✅ `(555) 123-4567` — space after paren (originally reported case)
- ✅ `(555)123-4567` — no space after paren
- ✅ `(555)-123-4567` / `(555).123.4567` — dash/dot after paren
- ✅ `555-123-4567`, `555.123.4567`, `+1 555 123 4567` — existing formats, no regression
- ✅ `+1 (555) 123-4567`, `1 (555) 123-4567` — country code + parens combined
- ✅ Multiple numbers in one string — both redacted
- ✅ `(12)` in unrelated text — correctly NOT matched (false-positive guard)
- ✅ Number at start and end of string — boundary anchors work correctly
- ⬜ Trailing punctuation (`(555) 123-4567.`) — to be tested before final merge
- ⬜ Inside quotes (`'(555) 123-4567'`) — to be tested before final merge
- ⬜ All-spaces separator (`555 123 4567`) — to be tested before final merge
- ⬜ SSN not matched as phone — to be tested before final merge
- ⬜ Position accuracy for parenthesized format — to be tested before final merge
