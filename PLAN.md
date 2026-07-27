## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers —
https://github.com/ascherj/pathreview/issues/146

### Understand
The `PIIScrubber` class in `safety/pii_scrubber.py` redacts personal info using
regex patterns. The `phone_us` pattern only allows a dash or dot between the
area code and the rest of the number, so it matches `555-123-4567` but not the
common parenthesized format `(555) 123-4567`.

- **Expected:** `scrub("(555) 123-4567")` returns `[REDACTED]`, and
  `detect("(555) 123-4567")` returns one phone match.
- **Actual:** the number passes through unchanged, and `detect()` returns 0.

Root cause (current pattern):
`\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b`
Two problems:
1. The separator `[-.]?` allows a dash or dot but **not a space**, so it chokes
   on the `) ` (close-paren + space) in `(555) 123-4567`.
2. The leading `\b` requires a word character at the start, so it fails when the
   text begins with `(`.

### Map
Files involved:
- `safety/pii_scrubber.py` — the `PII_PATTERNS["phone_us"]` regex (line ~15). **Only code change.**
- `tests/unit/test_pii_scrubber.py` — existing tests that pin the expected behavior (no change needed; they should pass after the fix).

### Plan
1. Allow whitespace as a separator: change `[-.]?` to `[-.\s]?` so `) 123` matches.
2. Loosen the boundaries: change the leading `\b` to `(?<!\w)` and the trailing
   `\b` to `(?!\w)` so a leading `(` is allowed without over-matching.
3. Run `pytest tests/unit/test_pii_scrubber.py -v` and confirm the four phone
   tests now pass.
4. Run the full unit suite to confirm no other tests regress.
5. Verify the dashed format `555-123-4567` and the `+1` prefix still work.

### Inputs & outputs
- **Input:** a string of text passed to `scrub()` or `detect()`.
- **Output:** `scrub()` returns the text with phone numbers (both dashed and
  parenthesized) replaced by `[REDACTED]`; `detect()` returns a list including
  those phone numbers with correct type and positions.

### Risks & unknowns
- A looser regex could over-match and redact things that aren't phone numbers
  (e.g. random digit groups). Keep the boundaries tight with lookarounds.
- Regex changes can interact unexpectedly with the `re.IGNORECASE` flag and word
  boundaries — must verify against all existing phone tests.
- Unsure whether other formats (e.g. `555.123.4567` with dots, or no separator)
  are also expected; will confirm by reading `tests/unit/test_pii_scrubber.py`.

### Edge cases
- `(555) 123-4567` — parenthesized with space (the bug).
- `555-123-4567` — dashed (must still work).
- `(555) 123-4567` at the very start of a string (word-boundary edge case).
- `555-123-4567` at the very start of a string (should still work — regression check).
- `+1 (555) 123-4567` — country code plus parentheses.
- Text with no phone number — should redact nothing.
