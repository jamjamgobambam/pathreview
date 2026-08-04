## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers —
[ascherj/pathreview#146](https://github.com/ascherj/pathreview/issues/146)

### Understand

**Root cause.** The `phone_us` regex in `safety/pii_scrubber.py` uses `[-.]?` as
the only separator between number groups:

```python
r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
```

`[-.]?` matches a hyphen, a dot, or nothing — but **never a space**. The very
common parenthesized area-code format writes a space after the closing paren
(`(555) 123-4567`), and the `+1`-prefixed international-style US format uses
spaces throughout (`+1 555 123 4567`). Because the pattern cannot consume that
space between the area code and the prefix, the match fails at that position and
the number is left untouched.

**Expected vs. actual.**

| Input | Expected | Actual (reproduced) |
| --- | --- | --- |
| `555-123-4567` | redacted | ✅ redacted |
| `555.123.4567` | redacted | ✅ redacted |
| `(555) 123-4567` | redacted | ❌ passes through, `detect()` returns `[]` |
| `+1 555 123 4567` | redacted | ❌ passes through, `detect()` returns `[]` |

This is a genuine privacy leak: any resume/profile that lists a phone number in
the parenthesized format is stored and displayed unredacted.

### Map

Files/functions involved:

- `safety/pii_scrubber.py` — `PIIScrubber.PII_PATTERNS["phone_us"]` is the one
  line that changes. `scrub()` and `detect()` both consume it, so fixing the
  pattern fixes both paths at once.
- `tests/unit/test_pii_scrubber.py` — the existing tests that define "done":
  `test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`. I may add one or two
  extra assertions for edge cases (see below), but no test rewrites are needed.

Files I expect to touch:
1. `safety/pii_scrubber.py` (the regex + remove the Week-8 BUG marker comment)
2. `tests/unit/test_pii_scrubber.py` (only if I add edge-case coverage)

### Plan

1. **Widen the separators to include whitespace.** Change each `[-.]?`
   separator (and the one inside the `+1` prefix group) to `[-.\s]?` so a single
   space is accepted between groups. Draft pattern:
   `r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"`.
2. **Verify the two failing formats now match** with a quick REPL check on
   `(555) 123-4567` and `+1 555 123 4567` for both `scrub()` and `detect()`.
3. **Run the full unit suite** (`pytest tests/unit/test_pii_scrubber.py -v`) and
   confirm the 4 phone tests flip to green with zero regressions on the email,
   SSN, and "no PII" tests.
4. **Guard against over-matching.** Add/confirm assertions that a bare SSN
   (`123-45-6789`) and a plain number sequence are not misclassified as a phone,
   and that `test_detect_no_false_positives` still passes.
5. **Clean up**: remove the `# BUG (issue #146 …)` reproduction comment and
   update `JOURNAL.md` (Week 9 entry) with the final diff/PR link.

### Inputs & outputs

- **Input:** an arbitrary text string passed to `PIIScrubber.scrub(text)` or
  `PIIScrubber.detect(text)`.
- **Output of `scrub()`:** the same string with every US phone number — in
  dash, dot, parenthesized, or `+1` space-separated form — replaced by
  `[REDACTED]`.
- **Output of `detect()`:** a list of dicts including a `phone_us` entry (with
  `type`, `value`, `start`, `end`) for each such number.
- **Net change:** one regex string; behavior for all non-phone PII types is
  unchanged.

### Risks & unknowns

- **Over-broadening.** Allowing `\s` as a separator could let the pattern span
  across unrelated adjacent numbers or accidentally match an SSN
  (`123-45-6789`). Mitigation: keep separators as optional *single*
  characters (`[-.\s]?`, not `\s*`), keep the `{3}{3}{4}` digit-group anchoring,
  and lean on `test_detect_no_false_positives` / the SSN tests as guardrails.
- **`\b` interaction with `(`.** A leading `(` is a non-word char, so the `\b`
  currently anchors just after it on the first digit. I need to confirm the
  widened pattern still matches when the phone is at the very start of the string
  (`test_phone_at_start_of_text`) — reproduction shows the current one already
  anchors there, so this should hold, but I'll re-verify.
- **Ordering vs. `phone_intl` and `ssn`.** Patterns run in dict order in
  `scrub()`. I need to confirm `phone_us` still wins/co-exists correctly with the
  `phone_intl` pattern for the `+1 …` case and doesn't double-redact oddly.
- **Unrelated pre-existing failure.** `test_mixed_pii_and_text` also fails, but
  because the greedy `street_address` regex redacts `"5 years developing Python
  appl…"` — that is **not** issue #146. I will leave it out of scope and note it
  so it isn't mistaken for a regression from my change.

### Edge cases

- Phone at the **start** of the string: `(555) 123-4567 is my number.`
- Phone at the **end** of the string: `My phone is 555-123-4567`
- **All four formats**: `555-123-4567`, `555.123.4567`, `(555) 123-4567`,
  `+1 555 123 4567`.
- **No space vs. one space** after the paren: `(555)123-4567` and `(555) 123-4567`.
- **Must NOT match**: a lone SSN `123-45-6789`, a version string `1.2.3`, and
  arbitrary 9/10-digit runs that aren't phone-shaped.
- **Empty / whitespace-only** input returns unchanged (already covered).
