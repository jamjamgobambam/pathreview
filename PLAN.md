## Solution plan

**Issue:** #146 — PII scrubber fails to redact parenthesized US phone numbers
https://github.com/ascherj/pathreview/issues/146

### Understand
The separators between digit groups ('[-.]') only allow an optional dash or dot, but never a space.`(555) 123-4567` uses a space after the closing parenthesis, not a dash, so the match fails there.
I confirmed this by testing `555 123 4567` (space-separated, no parens at all)
against the pattern directly, which also returns `None`, proving spaces (not
parentheses) are what's unhandled.

**Expected behavior:** `(555) 123-4567` should be matched and redacted like
any other US phone format.
**Actual behavior:** it passes through both `scrub()` and `detect()` completely
unredacted, because no separator variant in the pattern accepts whitespace.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
Files involved:
1. `safety/pii_scrubber.py` — `PIIScrubber.PII_PATTERNS["phone_us"]`. This is the only pattern I expect to change to fix this issue.

2. `tests/unit/test_pii_scrubber.py` — the four failing tests referenced in the
  issue: `test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`. I won't add new tests
  unless I find an edge case the existing four don't cover.


### Plan
1. Update the `phone_us` regex so each `[-.]?` separator also accepts a space
   E.g. changing `[-.]?` to `[-.\s]?` in both places between digit groups.
2. Also update the leading `(?:\+?1[-.]?)?` group the same way, since
   `test_us_phone_formats` includes `"+1 555 123 4567"` (space-separated with
   a country code prefix), which fails under the current pattern for the same
   reason.
3. Re-run my manual reproduction (`scrub()`/`detect()` on `(555) 123-4567`) to
   confirm it's now redacted and detected.
4. Run `.venv/bin/pytest tests/unit/test_pii_scrubber.py -v` to confirm all
   four previously-failing tests pass, and that no other test in the file
   regresses (especially `test_detect_no_false_positives`, since loosening
   the separator could increase false matches).
5. Run `make check` before committing the fix.


### Inputs & outputs
**Function:** `PIIScrubber.scrub(text: str) -> str` and
`PIIScrubber.detect(text: str) -> list[dict]`

- Input of both functions: a string that may contain a US phone number in any of: dashed
  (`555-123-4567`), dotted (`555.123.4567`), parenthesized-with-space
  (`(555) 123-4567`), or country-code-prefixed with spaces
  (`+1 555 123 4567`).

- Output of `scrub()`: the same string with any matched phone number replaced
  by `[REDACTED]`.

- Output of `detect()`: a list of dicts, each with `type: "phone_us"`,
  `value`, `start`, `end` for every match found.

### Risks & unknowns
`[-.\s]?` only allows a single separator character, so double spaces
between groups won't match. None of the four failing tests require this,
so treating it as out of scope for now.

### Edge cases
- `(555) 123-4567` — primary case from the issue, must be redacted.
- `+1 555 123 4567` — space-separated with country code, covered by
  `test_us_phone_formats`.
- `555 123 4567` — space-separated, no parens; same root cause, should also
  be caught by the fix.
- `(555)-123-4567` — already works today, must not regress.