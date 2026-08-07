# Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146) — #146 (Tier 1, `safety`)

### Understand

The `phone_us` pattern in `safety/pii_scrubber.py` is:

```
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
```

The **root cause** is the separator classes: between the (optionally
parenthesized) area code and the exchange digits it allows only an *optional*
`[-.]`. In the very common `(555) 123-4567` form there is a **space** after the
`)`, and the pattern has no way to consume it, so matching fails right after the
area code. The same limitation breaks other space-separated forms such as
`+1 555 123 4567`.

- **Expected:** `scrub("(555) 123-4567")` returns `"[REDACTED]"`, and
  `detect("(555) 123-4567")` returns one `phone_us` entry with accurate
  `start`/`end`.
- **Actual:** `scrub()` returns the number unchanged and `detect()` returns
  `[]` — a real safety leak, since the module exists to strip PII before text
  reaches the model.

### Map

Files I expect to touch:

- **`safety/pii_scrubber.py`** — the *only* production change: the
  `PII_PATTERNS["phone_us"]` regex string. `scrub()` and `detect()` consume the
  pattern unchanged, so no logic changes are needed there.
- **`tests/unit/test_pii_scrubber.py`** — the four tests that already define
  "done" (`test_us_phone_number_redaction`, `test_us_phone_formats`,
  `test_detect_phone_pii`, `test_phone_at_start_of_text`). I may add one focused
  regression test for `(555) 123-4567` covering both `scrub()` and `detect()`.

Read-only reference (no edits expected):

- Callers of `PIIScrubber` in the `safety` layer, to confirm nothing depends on
  the current numbered capture groups `([0-9]{3})...` or on the buggy behavior.

### Plan

1. **Broaden the separators** in `phone_us` so the area-code → exchange and
   exchange → line-number joins accept a space as well as `-`/`.` (and handle
   the `(555) ` case), while still matching the working `555-123-4567` and
   `555.123.4567` forms.
2. **Verify the leading boundary** still works when the string starts with `(`
   (word boundary sits before the first digit), so `test_phone_at_start_of_text`
   passes.
3. **Run the four target tests, then the full `tests/unit/test_pii_scrubber.py`**
   to confirm the fix and catch regressions (especially `test_text_with_no_pii`,
   `test_detect_no_false_positives`, and the dashed/dotted-format tests).
4. **Add a targeted regression test** for the parenthesized form in both
   `scrub()` and `detect()` if existing coverage leaves a gap.
5. **Lint/format** the file (`ruff`, `black`) and keep the production diff scoped
   to the single regex line.

### Inputs & outputs

- **Input:** arbitrary user-supplied text passed to `PIIScrubber.scrub(text)`
  and `PIIScrubber.detect(text)`.
- **Output / change:** parenthesized and space-separated US phone numbers are
  replaced with `[REDACTED]` by `scrub()` and reported by `detect()` (type
  `phone_us`, correct `start`/`end`). Non-phone text and already-working formats
  are unchanged; `scrub()` stays idempotent.

### Risks & unknowns

- **Over-broadening → false positives.** Loosening separators could match
  non-phone digit runs (dates, version strings, "5 123 4567"). Guarded by
  `test_text_with_no_pii`, `test_detect_no_false_positives`, and
  `test_scrub_idempotent`.
- **`\s` spans newlines.** If I allow `\s` between groups it could bridge two
  unrelated numbers across lines. Mitigation: use a space-only/bounded separator
  (e.g. `[ ]` or a limited `[-.\s]`) and test multiline input.
- **`detect()` positions.** `start`/`end` must stay accurate after the pattern
  changes.
- **Unknown — `+1 555 123 4567` ownership.** `test_us_phone_formats` includes
  this form, so either `phone_us` or `phone_intl` must cover it; I'll decide
  which pattern owns it during implementation.
- **Out of scope (noted, won't fix here):** `test_mixed_pii_and_text` currently
  fails for an *unrelated* reason — the `street_address` regex over-matches
  (`"Pl"` inside "app**pl**ications" redacts "Python"). That is a separate bug,
  not #146; I flag it only so I don't mistake it for a regression I introduced.

### Edge cases

- Formats: `(555) 123-4567`, `(555)123-4567` (no space), `555-123-4567`,
  `555.123.4567`, `+1 555 123 4567`, `+1 (555) 123-4567`.
- Position: phone at the start of text, at the end, and embedded mid-sentence.
- Non-PII text stays byte-for-byte unchanged; double-scrub is idempotent.
- Multiline text so the separator doesn't bridge two separate numbers.
