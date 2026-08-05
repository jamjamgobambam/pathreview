# PLAN.md - Planning Framework

## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers #146](https://github.com/ascherj/pathreview/issues/146)

### Understand

**Root cause.** The bug is in the `phone_us` regex in `safety/pii_scrubber.py:22`:

```
\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b
```

Decrypted piece by piece:

| Fragment | Meaning |
|----------|---------|
| `\b` | word boundary |
| `(?:\+?1[-.]?)?` | optional `+1` country code, then optional `-` or `.` |
| `\(?` | optional opening `(` |
| `([0-9]{3})` | area code |
| `\)?` | optional closing `)` |
| `[-.]?` | separator — **only `-` or `.`** |
| `([0-9]{3})` | exchange |
| `[-.]?` | separator — **only `-` or `.`** |
| `([0-9]{4})` | line number |
| `\b` | word boundary |

My note in `pii_scrubber.py` guessed the parentheses weren't matched. Investigating the regex shows the opposite: `\(?` / `\)?` handle parens correctly — `(555)123-4567` (no space) *does* redact. **The actual root cause is that the separator classes `[-.]?` do not include whitespace.** The two failing formats — `(555) 123-4567` and `+1 555 123 4567` — both rely on a **space** as a separator, so matching breaks at the first space.

**Expected vs. actual.** Expected: all four formats in `test_us_phone_formats` (`test_pii_scrubber.py:47`) are redacted. Actual: hyphen/dot formats redact; space-separated formats (parenthesized `(555) 123-4567` and `+1 555 123 4567`) pass through untouched.

Verified empirically: `pytest tests/unit/test_pii_scrubber.py` → 4 phone tests fail (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`). A 5th failure, `test_mixed_pii_and_text`, is **out of scope** — it's caused by the greedy `street_address` regex redacting "Python appl…" (matches the `Pl` alternation), not by phones. My comment in the test file already flags this one as unrelated.

### Map

- **File to change:** `safety/pii_scrubber.py` — only the `PII_PATTERNS["phone_us"]` regex string (line 22). No changes to `scrub()` or `detect()` logic are needed; both iterate the pattern dict generically.
- **Test file (verify only, no change expected):** `tests/unit/test_pii_scrubber.py` — the 4 phone tests must pass; the 20 currently-passing tests must stay green.
- **Not touched:** the `street_address` false-positive causing `test_mixed_pii_and_text` to fail is a separate issue and stays out of scope.

Expected files touched: **`safety/pii_scrubber.py`** (one line).

### Plan

1. **Reproduce.** Run `pytest tests/unit/test_pii_scrubber.py` and confirm the 4 phone failures (done — baseline captured).
2. **Fix the separators.** Allow a space (or hyphen/dot) between every group in `phone_us`: replace the two `[-.]?` separators with `[-.\s]?` (or a literal-space class `[-. ]?`), and update the country-code separator `\+?1[-.]?` → `\+?1[-.\s]?` so `+1 555 …` also matches.
3. **Verify targeted tests.** Re-run the file; confirm the 4 phone tests pass and no previously-passing test regresses (especially `test_text_with_no_pii` and `test_detect_no_false_positives`, which guard against over-matching).
4. **Guard against over-broad matching.** Spot-check that broadening to whitespace doesn't newly redact benign digit strings (e.g. version numbers, "100 200 3000"); prefer a literal space over `\s` if `\s` proves too greedy across newlines/tabs.
5. **Document.** Note in JOURNAL.md that the root cause was the missing whitespace separator (not the parentheses, as first hypothesized).

### Inputs & outputs

- **Input:** arbitrary text passed to `PIIScrubber.scrub(text)` / `PIIScrubber.detect(text)` containing US phone numbers in mixed formats (hyphen, dot, space, parenthesized, with/without `+1`).
- **Output / change:** `scrub()` replaces every US phone format — now including `(555) 123-4567` and `+1 555 123 4567` — with `[REDACTED]`; `detect()` returns a `phone_us` entry (type/value/start/end) for those same formats. The only artifact changed is the one regex string.

### Risks & unknowns

- **Over-matching.** Adding `\s` to separators risks redacting non-phone digit sequences separated by spaces (e.g. "call 100 200 3000", quantities, IDs). `\s` also matches newlines/tabs, so a number split across lines could match unintentionally — a literal-space class `[-. ]?` is safer.
- **Interaction with `phone_intl`.** `+1 555 123 4567` could be caught by either `phone_us` or `phone_intl`; since both redact to `[REDACTED]` this is harmless, but detect() may report overlapping matches — acceptable for this issue.
- **Unknown:** whether reviewers want the captured groups cleaned up (the current match can include a stray `)`), or whether stricter formats (e.g. exactly one separator style) are desired. Scoping to "make the 4 tests pass without regressions" is the safe default.
- **Out of scope but present:** the `street_address` greedy-match failure (`test_mixed_pii_and_text`) — I will not fix it here and must confirm my change doesn't alter its behavior.

### Edge cases

- Space after the paren: `(555) 123-4567` (the headline case).
- Space-separated throughout: `555 123 4567`, `+1 555 123 4567`.
- Existing passing formats must stay working: `555-123-4567`, `555.123.4567`, `(555)123-4567`.
- Phone at start of text (no leading word char before it) — `test_phone_at_start_of_text`.
- Empty string and whitespace-only input → returned unchanged (`test_empty_text`, `test_whitespace_only`).
- Text with no PII → returned unchanged, no false positives (`test_text_with_no_pii`, `test_detect_no_false_positives`).
- Idempotency: scrubbing already-scrubbed text is a no-op (`test_scrub_idempotent`).