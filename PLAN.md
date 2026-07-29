## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers — https://github.com/ascherj/pathreview/issues/146

### Understand

**Root cause.** The `phone_us` regex in `safety/pii_scrubber.py` (line 15) uses
`[-.]?` as the separator between the number groups:

```
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
```

`[-.]?` only matches an optional dash or dot — it does **not** match a space.
Common US formats put a space after the area code (`(555) 123-4567`) or between
every group (`+1 555 123 4567`), so those strings never match and pass through
un-redacted.

**Expected vs. actual.**
- Expected: `scrub("(555) 123-4567")` → `"[REDACTED]"`, and `detect()` returns a
  `phone_us` entry.
- Actual: the parenthesized/space-separated number is returned unchanged and
  `detect()` returns `count=0`. Confirmed by 4 failing tests plus a dedicated
  reproduction test (`test_repro_issue_146_parenthesized_phone`).

### Map

Files/functions involved:
- **`safety/pii_scrubber.py`** — `PIIScrubber.PII_PATTERNS["phone_us"]` (the
  regex to change). Both `scrub()` and `detect()` consume this same pattern, so
  one regex change fixes both methods.
- **`tests/unit/test_pii_scrubber.py`** — the tests that define "correct":
  `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
  `test_phone_at_start_of_text`, plus my `test_repro_issue_146_parenthesized_phone`
  and the guard tests `test_text_with_no_pii` / `test_detect_no_false_positives`.

Files I expect to touch:
1. `safety/pii_scrubber.py` (the fix — one regex line).
2. `tests/unit/test_pii_scrubber.py` (only if I find an untested realistic format
   worth adding; the reproduction test already lives here).

### Plan

1. **Widen the separator.** Replace the two `[-.]?` separators (and the one after
   `+1`) with a character class that also allows whitespace — conceptually
   dash / dot / space — so `(555) 123-4567`, `555.123.4567`, and `+1 555 123 4567`
   all match.
2. **Re-check the parenthesized branch.** Make sure `\(?([0-9]{3})\)?` plus the
   new separator handles the space that sits *between* `)` and the next digits.
3. **Run the phone tests** (`pytest -k phone`) until all 4 original tests + the
   reproduction test pass.
4. **Run the guard tests** (`test_text_with_no_pii`, `test_detect_no_false_positives`)
   and the full `test_pii_scrubber.py` file to confirm no regressions in email /
   SSN / address handling.
5. **Run `make check && make test-unit`** before opening the PR, per CONTRIBUTING.

### Inputs & outputs

- **Input:** an arbitrary text string passed to `scrub(text)` or `detect(text)`.
- **Output of `scrub`:** the same string with every US phone number — dashed,
  dotted, parenthesized, or space-separated — replaced by `[REDACTED]`.
- **Output of `detect`:** a list including a `{"type": "phone_us", ...}` entry for
  each phone number, with accurate `start`/`end` positions.
- **What changes:** only the `phone_us` regex string. No function signatures, no
  public behavior beyond "more phone formats now caught."

### Risks & unknowns

- **False positives (main risk).** Allowing spaces as separators makes the pattern
  looser and could match non-phone digit sequences (e.g. `123 456 7890` inside an
  ID, or spaced numbers in prose). `test_detect_no_false_positives` (version
  `1.2.3`) and `test_text_with_no_pii` are the tripwires — I must keep them green.
- **Greedy whitespace.** Using `\s` matches newlines/tabs too, which could let a
  phone number span line breaks in unexpected ways. May need to restrict to a
  literal space rather than full `\s`.
- **`\b` word-boundary interaction.** The trailing `\b` after `([0-9]{4})` and the
  leading `\b` may behave differently now that a space can precede digits; I need
  to verify `test_phone_at_start_of_text` still passes.
- **Unknown:** whether the maintainer prefers one broadened `phone_us` pattern or
  a separate explicit pattern for the parenthesized form — I'll keep it to one
  pattern unless review says otherwise.

### Edge cases

- `(555) 123-4567` — space after `)` (the reported case).
- `+1 555 123 4567` — leading country code and all-space separators.
- `555.123.4567` — dotted separators (must still work).
- `555-123-4567` — dashed separators (must not regress).
- `(555)123-4567` — parentheses with **no** space (should still match).
- Phone at the very start of the text (`test_phone_at_start_of_text`).
- Non-phone digit runs like version `1.2.3` and normal prose — must **not** be
  redacted.
