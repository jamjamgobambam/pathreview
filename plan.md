## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers #146](https://github.com/ascherj/pathreview/issues/146)

### Understand

**Actual behavior:** `scrub('Call me at (555) 123-4567')` returns the string unchanged; `detect('Call me at (555) 123-4567')` returns `[]`.

**Expected behavior:** Both methods treat `(555) 123-4567` the same way they treat `555-123-4567` — the scrubber replaces it with `[REDACTED]` and the detector reports it as `phone_us` PII.

**Root causes (two):**

1. **Word-boundary anchor at start.** The original pattern begins with `\b`. When a phone starts with `(` preceded by a space, both characters are non-word characters (`\W`), so no word boundary exists and the pattern never starts matching.

2. **Separator class too narrow.** The original pattern uses `[-.]?` between the area code and exchange. The parenthesized format `(555) 123-4567` has a space in that position, which the class does not include.

A third, pre-existing bug was also found: the `street_address` pattern used `[A-Za-z\s]+` (arbitrary characters including spaces) before the street-type alternation, which allowed short abbreviations like `Pl` to match sub-strings inside ordinary words (e.g., `applications`). This caused `test_mixed_pii_and_text` to fail.

### Map

Files to touch:

- `safety/pii_scrubber.py` — the only file that needs editing; both regex constants live in `PIIScrubber.PII_PATTERNS`
- `tests/unit/test_pii_scrubber.py` — read-only during this fix; all 25 tests must pass after the change

No other files are involved. The `scrub()` and `detect()` methods iterate over `PII_PATTERNS` generically, so no logic changes are needed — only the pattern strings.

### Plan

1. **Replace `\b` anchors in `phone_us` with lookaround assertions.**
   Change the leading `\b` to `(?<!\w)` (negative lookbehind: not preceded by a word character) and the trailing `\b` to `(?!\w)` (negative lookahead). This correctly handles both "no preceding character" (start of string) and "preceded by whitespace" without requiring a word-character on the left side.

2. **Widen the separator character class.**
   Change every `[-.]?` in `phone_us` to `[-. ]?` so that a space is a valid separator between the area code, exchange, and subscriber segments.

3. **Fix the `street_address` false-positive.**
   Replace the greedy `[A-Za-z\s]+` (which can match partial words) with `(?:[A-Za-z]+\s+)*` (zero or more complete alpha words each followed by whitespace). Add `\b` after the street-type alternation so abbreviations like `Pl` only match at a genuine word boundary, not as a sub-string inside `applications`.

4. **Run the full test suite.**
   `pytest tests/unit/test_pii_scrubber.py -v -m unit` must show 25 passed, 0 failed.

5. **Commit and push.**
   Commit with message `fix(safety): support parenthesized US phone format in pii_scrubber` per the Conventional Commits convention in `docs/CONTRIBUTING.md`.

### Inputs & outputs

**Input to the fix:** the two string constants in `PIIScrubber.PII_PATTERNS` (`phone_us` and `street_address`).

**Output / observable change:**
- `scrub('Call me at (555) 123-4567 or 555-123-4567')` → `'Call me at [REDACTED] or [REDACTED]'`
- `detect('Call me at (555) 123-4567')` → list containing one entry with `type='phone_us'`
- `scrub('I worked at TechCorp for 5 years developing Python applications.')` no longer redacts "Python applications"

### Risks & unknowns

- **Space separator and false positives.** Adding ` ` to `[-.]?` means three space-separated groups of digits could be mistaken for a phone number. In practice this is low-risk because the pattern requires exactly 10 digits in a 3-3-4 split, which is uncommon in non-phone contexts. The existing `test_detect_no_false_positives` test (version numbers, URLs) still passes.
- **`street_address` regression.** Narrowing `[A-Za-z\s]+` to `(?:[A-Za-z]+\s+)*` could miss street names that contain unusual formatting. All three address tests in the suite (`test_street_address_redaction`, `test_address_variations`) pass with the new pattern.

### Edge cases

- Phone at start of string with no preceding character: `(555) 123-4567 is my phone` — `(?<!\w)` matches at start of string.
- Phone preceded by a non-word character other than space (e.g., colon): `Phone:(555) 123-4567` — `:` is `\W`, so `(?<!\w)` still matches.
- Phone embedded inside a longer digit sequence: `12345551234567` — `(?<!\w)` fails because `4` precedes the first `5`; correctly not matched.
- Country code with space: `+1 555 123 4567` — `(?:\+?1[-. ]?)?` matches `+1 ` and the space separators handle the rest.
- Mixed formats in same string: `(555) 123-4567 or 555-123-4567` — both are matched and redacted independently.