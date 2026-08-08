# Reproduction — Issue #146

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

**Location of the bug:** `safety/pii_scrubber.py`, the `phone_us` entry in the
`PII_PATTERNS` dict (line 15). Its separator character class `[-.]?` allows a
dash or a dot between number groups, but **not a space** — so any US phone number
written with a space after the area code (the `(555) 123-4567` and
`+1 555 123 4567` formats) is never matched.

## How to reproduce

These are pure unit tests on a regex — no Docker, database, or frontend needed.

### 1. Run the affected test file

```bash
./.venv/Scripts/pytest tests/unit/test_pii_scrubber.py -v      # Windows (Git Bash)
# ./.venv/bin/pytest tests/unit/test_pii_scrubber.py -v        # macOS / Linux
```

**Observed result:** the following four tests fail, all because a parenthesized
or space-separated phone number is left in the text instead of being redacted:

- `test_us_phone_number_redaction`
- `test_us_phone_formats`
- `test_detect_phone_pii`
- `test_phone_at_start_of_text`

Representative failure:

```
test_phone_at_start_of_text
>   assert "[REDACTED]" in scrubbed
E   AssertionError: assert '[REDACTED]' in '(555) 123-4567 is my phone number.'
```

### 2. Minimal reproduction (the snippet from the issue)

```bash
./.venv/Scripts/python -c "from safety.pii_scrubber import PIIScrubber; s=PIIScrubber(); print(repr(s.scrub('Call me at (555) 123-4567 or 555-123-4567'))); print(s.detect('Call me at (555) 123-4567'))"
```

**Observed output:**

```
'Call me at (555) 123-4567 or [REDACTED]'   # (555) 123-4567 NOT redacted; dashed one IS
[]                                          # detect() finds no PII at all
```

**Expected output:** both phone numbers should be replaced with `[REDACTED]` in
`scrub()`, and `detect()` should return one phone entry for `(555) 123-4567`.

## Out of scope (not part of this issue)

Running the file also shows a fifth failure, `test_mixed_pii_and_text`. That one
fails on `assert "Python" in scrubbed` because a *different* pattern — the
over-broad `street_address` regex — wrongly redacts "Python ap**pl**ications"
(it matches the "pl" in "applications" as the "Pl"/Place street suffix). This is
a separate pre-existing bug, unrelated to the phone-number issue #146, and is
intentionally left untouched by this fix.
