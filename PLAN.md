## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers — #146](https://github.com/ascherj/pathreview/issues/146)

### Understand

The `PIIScrubber` class detects and redacts PII using a dictionary of regex
patterns. The `phone_us` pattern is:

```
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
```

**Root cause:** the separator between number groups is the character class
`[-.]?`, which matches a hyphen or a dot but **not a space**. Common US phone
formats put a space after the area code — `(555) 123-4567` — or use spaces
throughout — `+1 555 123 4567`. Because the pattern cannot consume that space,
the regex fails to match those numbers.

**Expected vs. actual:**

| Input | Expected `scrub()` | Actual `scrub()` |
|---|---|---|
| `(555) 123-4567` | `[REDACTED]` | `(555) 123-4567` (unchanged) |
| `555-123-4567` | `[REDACTED]` | `[REDACTED]` (already works) |
| `+1 555 123 4567` | `[REDACTED]` | `+1 555 123 4567` (unchanged) |

`detect()` uses the same pattern, so it returns an empty list for a
parenthesized number instead of reporting one phone-number match. This is a
privacy leak: one of the most common phone formats flows through the safety
layer un-redacted.

### Map

Files/functions involved:

- **`safety/pii_scrubber.py`** — the only file the fix changes.
  - `PIIScrubber.PII_PATTERNS["phone_us"]` (line 15) — the regex to update.
  - `PIIScrubber.scrub()` (line 21) — consumes the pattern via `re.sub`.
  - `PIIScrubber.detect()` (line 37) — consumes the pattern via `re.finditer`.
- **`tests/unit/test_pii_scrubber.py`** — the verification target. Not expected
  to be modified; these tests should turn green once the pattern is fixed:
  `test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`.

### Plan

1. **Widen the separator** in the `phone_us` pattern so a single optional
   whitespace character is accepted wherever a `-`/`.` separator can appear —
   change each `[-.]?` to `[-.\s]?`, including the one after the optional
   `(?:\+?1 ...)` country code, so `) ` and all-spaces formats match.
2. **Verify the target tests pass:** run
   `./.venv/Scripts/pytest tests/unit/test_pii_scrubber.py -v` and confirm the
   four phone tests listed above now pass.
3. **Guard against regressions:** confirm the 20 previously-passing tests still
   pass — especially `test_text_with_no_pii`, `test_detect_no_false_positives`,
   and the dashed/dotted formats — so the wider pattern didn't start matching
   non-phone text.
4. **Run the quality gate:** `make check` (ruff + black + mypy) and let the
   pre-commit hooks format/lint the change; ensure it is clean.
5. **Commit + PR (Week 9):** commit with a Conventional Commit message such as
   `fix(safety): redact space-separated and parenthesized US phone numbers`
   referencing #146, push, and open the PR using the repo template.

### Inputs & outputs

- **Input:** arbitrary text strings passed to `PIIScrubber.scrub(text)` and
  `PIIScrubber.detect(text)`.
- **Output / change:** the fix only edits the `phone_us` regex string. After the
  change, `scrub()` returns the input with every common US phone format replaced
  by `[REDACTED]`, and `detect()` returns a dict entry
  (`type="phone_us"`, `value`, `start`, `end`) for each such number. No function
  signatures, return types, or other patterns change.

### Risks & unknowns

- **Over-broadening the pattern.** Adding `\s` risks matching across unintended
  boundaries (e.g. spanning a newline, or gluing two unrelated number groups
  separated by spaces). Mitigation: allow at most **one** optional whitespace per
  separator (`[-.\s]?`, not `[-.\s]*`) and keep the `\b` word-boundary anchors.
  Verify with `test_text_with_no_pii` and `test_detect_no_false_positives`.
- **Leading `\b` vs. a leading `(`.** For `(555) 123-4567` the `\b` sits before
  the `5`, so the `(` may fall outside the match. That is acceptable — the digits
  are still redacted — but I need to confirm `detect()` still returns a sensible
  `value`/`start`/`end`, and that `[REDACTED]` replaces the number.
- **Country-code branch.** `+1 555 123 4567` requires the optional
  `(?:\+?1[-.]?)?` group to also accept a space; I need to update that separator
  too, not just the two between the main groups.
- **Unknown:** whether a stricter, more explicit multi-alternation pattern would
  be safer than simply adding `\s`. I'll start with the minimal `\s` change and
  only escalate if a regression appears.

### Edge cases

The fix should handle these gracefully (all covered by existing tests unless
noted):

- `(555) 123-4567` — parenthesis + space (the reported bug).
- `+1 555 123 4567` — country code with all-space separators.
- `555-123-4567` and `555.123.4567` — must keep working (no regression).
- Phone at the very start of the text, and at the very end.
- Multiple phone numbers in one string.
- Text with **no** phone number — plain numbers like `version 1.2.3` or a URL
  must NOT be redacted (no false positives).
- Empty string and whitespace-only string — return unchanged, no crash.
- **Out of scope:** the unrelated `test_mixed_pii_and_text` failure caused by the
  over-broad `street_address` regex is a separate issue and will not be addressed
  here.
