## Solution plan

**Issue:** [#146 — PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand
`PIIScrubber.PII_PATTERNS["phone_us"]` in `safety/pii_scrubber.py` is a single regex used
by both `scrub()` and `detect()`. The original pattern was:

```
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
```

The separator classes between digit groups (`[-.]?`) only allow a dash or a dot, not a
space. So `(555) 123-4567` — a closing paren, a space, then the rest of the number — never
matches: the space right after `)` breaks the match before it can even reach the area-code
group. Because `scrub()` and `detect()` both iterate over the same `PII_PATTERNS` dict and
run `re.sub`/`re.finditer` against it, the bug affects both entry points identically: the
number isn't redacted *and* isn't reported as detected PII.

I confirmed this locally with `scripts/repro_146.py` (see Reproduction below): running the
old pattern against `"Call me at (555) 123-4567 or 555-123-4567"` redacts only the dashed
number and leaves the parenthesized one in plaintext.

Root cause: the separator character class between the closing paren and the next digit
group didn't include whitespace, and the leading `\b` word boundary also silently prevented
`+1 555 123 4567` from matching (a leading `+` is not a word character, so `\b` never
matches there — same underlying "pattern doesn't account for the actual variety of
real-world input" root cause).

**Expected vs. actual:**
- Expected: `(555) 123-4567`, `555-123-4567`, `555.123.4567`, and `+1 555 123 4567` are all
  redacted by `scrub()` and reported by `detect()`.
- Actual (pre-fix): only the dash/dot-separated and the `\(?...\)?` — no-space forms
  matched; the space-separated parenthesized form and the `+1 ...` form did not.

### Map
Files involved:
- `safety/pii_scrubber.py` — `PIIScrubber.PII_PATTERNS["phone_us"]` (the regex itself,
  used by both `scrub()` and `detect()`). This is the only production file that needs a
  change.
- `tests/unit/test_pii_scrubber.py` — the four tests that pin down expected behavior:
  `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
  `test_phone_at_start_of_text`.
- `scripts/repro_146.py` — new reproduction script I added; not part of the fix, but
  documents the bug and verifies the fix against the old pattern side by side.
- `JOURNAL.md` — Week 7/8 entries tracking issue selection and reproduction.

### Plan
1. Reproduce the bug in isolation: run the *old* `phone_us` regex against sample strings
   (`(555) 123-4567`, `+1 555 123 4567`) outside the app to confirm exactly which formats
   fail, without needing the full Docker stack running. (Done — `scripts/repro_146.py`.)
2. Identify the minimal regex change: extend the separator character classes from
   `[-.]?` to `[-.\s]?` so a space is accepted between digit groups, matching the same
   spot where a dash or dot was already accepted.
3. Fix the leading anchor: the original `\b` fails on inputs like `+1 555 123 4567` because
   `+` isn't a word character. Replace it with a negative lookbehind `(?<!\d)` so the match
   isn't required to start at a word boundary, only that it isn't preceded by another digit
   (avoids matching in the middle of a longer digit run).
4. Run `pytest tests/unit/test_pii_scrubber.py -q` and confirm the four target tests pass:
   `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
   `test_phone_at_start_of_text`.
5. Run the full `tests/unit/` suite to check for regressions in unrelated tests before
   calling the fix done.

(Steps 1–4 are already implemented in commit `06230ad` on this branch; step 5 surfaced an
unrelated pre-existing bug — see Risks below.)

### Inputs & outputs
**Function/data changed:** `PIIScrubber.PII_PATTERNS["phone_us"]` (a class-level regex
string), consumed by `scrub(text: str) -> str` and `detect(text: str) -> list[dict]`.

- Input: free-form text that may contain a US phone number in one of: `555-123-4567`,
  `(555) 123-4567`, `555.123.4567`, `+1 555 123 4567`.
- Output of `scrub()`: the same text with every matched phone number replaced by
  `"[REDACTED]"`.
- Output of `detect()`: a list of dicts (`{"type": "phone_us", "value": ..., "start": ...,
  "end": ...}`) — one entry per matched number, now including the previously-missed
  formats.
- No change to function signatures, return types, or the `email`/`ssn`/`street_address`
  patterns.

### Risks & unknowns
1. **Looser separator matching could over-match.** Allowing `\s` as a separator means
   `555 123 4567` inside a longer run of numbers (e.g. a table of scores) could be
   misidentified as a phone number. Existing tests don't cover this; worth adding a
   negative test case if this comes up in review.
2. **`(?<!\d)` vs `\b` changes boundary behavior at the *end* of the match too** — I only
   changed the leading anchor, but should double check the trailing `\b` still correctly
   rejects things like `5551234567890` (an 11+ digit run) so it doesn't partially match.
   Confirmed via `test_us_phone_formats`/`test_phone_at_start_of_text` passing, but no
   explicit test for "too many trailing digits."
3. **Unrelated pre-existing bug found during full-suite regression run:**
   `test_mixed_pii_and_text` in `tests/unit/test_pii_scrubber.py` fails independently of
   this fix — the `street_address` pattern's `Pl` (Place) alternative matches
   case-insensitively inside unrelated words like "applications" (`aPPLications`),
   redacting `"5 years developing Python applications"` down to
   `"developing [REDACTED]ications"`. This is out of scope for #146 (it's in
   `street_address`, not `phone_us`) but I'm flagging it as a real risk in the same file —
   worth its own issue rather than silently fixing it as a drive-by change here.

### Edge cases
- `(555) 123-4567` — parenthesized area code with a space before the next group (the
  original bug): must be redacted/detected.
- `+1 555 123 4567` — leading `+1` with spaces throughout, no parens: must be redacted
  (was also broken by the `\b` anchor issue).
- `555-123-4567` and `555.123.4567` — dash/dot separated, already worked, must keep working
  (no regression).
- A phone number at the very start of a string (`test_phone_at_start_of_text`) and at the
  very end (`test_phone_at_end_of_text`) — anchor changes must not break either position.
