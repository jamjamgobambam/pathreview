## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers
https://github.com/ascherj/pathreview/issues/146

### Understand
The `phone_us` regex in `safety/pii_scrubber.py` starts with a `\b` word
boundary at the very beginning of the pattern. A `\b` only matches at a
transition between a word character and a non-word character. For input
like `(555) 123-4567`, the character before `(` is a space (non-word) and
`(` is also non-word, so no boundary exists there and the match never
starts. The dashed format (`555-123-4567`) works because the character
before the digit is a space (non-word) next to a digit (word char), which
is a valid boundary. Expected behavior: both `scrub()` and `detect()`
should recognize parenthesized and whitespace-separated formats
(`(555) 123-4567`, `+1 555 123 4567`) the same way they already handle
dashed and dotted formats. Actual behavior: those formats pass through
`scrub()` unredacted and are invisible to `detect()`.

### Map
- `safety/pii_scrubber.py` — the `PII_PATTERNS["phone_us"]` regex, and the
  `scrub()` and `detect()` methods that consume it (no changes needed here
  beyond the pattern itself, since both methods just iterate the pattern
  dict generically).
- `tests/unit/test_pii_scrubber.py` — `test_us_phone_number_redaction`,
  `test_us_phone_formats`, `test_detect_phone_pii`,
  `test_phone_at_start_of_text` define the expected behavior.

### Plan
1. Move the `\b` boundary check to after the optional opening parenthesis,
   so the boundary evaluates the transition into the digits, not into the
   parenthesis itself.
2. Widen the separators between digit groups (`[-.]?`) to also accept
   whitespace (`[-.\s]?`), covering `(555) 123-4567` and
   `+1 555 123 4567`.
3. Run the four named tests plus the full `test_pii_scrubber.py` suite to
   confirm the fix and check for regressions in unrelated patterns
   (email, SSN, address, international phone).
4. Run `ruff`/`black`/`mypy` via pre-commit to catch any lint issues in
   the touched file.
5. Confirm any remaining test failures are pre-existing and out of scope
   before committing (checked via `git stash` against `main`).

### Inputs & outputs
Input: raw text strings potentially containing US phone numbers in any of
four formats (dashed, dotted, parenthesized, whitespace-separated, with or
without a `+1`/`1` prefix). Output: `scrub()` returns the text with all
matched formats replaced by `[REDACTED]`; `detect()` returns a list of
`{type, value, start, end}` dicts for every matched format, with `type`
always `"phone_us"`.

### Risks & unknowns
- Widening the separator regex to allow whitespace could introduce false
  positives if plain text happens to contain three digit groups separated
  by spaces (e.g. version numbers or unrelated numeric sequences). Mitigated
  by keeping the exact `{3}-{3}-{4}` digit-group shape, which is fairly
  specific.
- The existing `phone_intl` pattern overlaps with `phone_us` for `+1 ...`
  inputs; need to confirm both patterns don't double-count the same match
  in `detect()` in a way that breaks `test_detect_no_false_positives`.
- Found the `street_address` pattern has an unrelated pre-existing bug
  (falsely matches `"pl"` inside `"applications"`), confirmed present on
  `main` via `git stash`. Left out of scope for this fix; flagging as a
  separate issue rather than fixing here.

### Edge cases
- Phone number at the very start or end of a string (already covered by
  `test_phone_at_start_of_text` / `test_phone_at_end_of_text`).
- Multiple phone numbers in the same string, in different formats.
- A `+1` prefix combined with parentheses, e.g. `+1 (555) 123-4567`.
- Numbers embedded in larger text where the fix must not swallow
  surrounding words (guarded by keeping the trailing `\b`).