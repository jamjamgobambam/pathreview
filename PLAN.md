## Solution plan

**Issue:** #146 — PII scrubber fails to redact parenthesized US phone numbers
(https://github.com/ascherj/pathreview/issues/146)

### Understand
The root cause is the `phone_us` regex in `safety/pii_scrubber.py`. Its separator groups (`[-.]?`) only allow a dash, a dot, or nothing between number segments. The common US format `(555) 123-4567` has a space after the closing parenthesis, which the separator does not accept, so the match fails. Expected: `scrub()` replaces the number with `[REDACTED]` and `detect()` reports a `phone_us` match.
Actual: The number passes through untouched and `detect()` returns an empty list.

### Map
- `safety/pii_scrubber.py` — specifically the `phone_us` entry in the `PII_PATTERNS` dictionary (the regex I will modify). The `scrub()` and `detect()` methods consume this pattern but will not need changes themselves.
- `tests/unit/test_pii_scrubber.py`
These are the four failing tests I must turn green:
  - `test_us_phone_number_redaction`
  - `test_us_phone_formats`
  - `test_detect_phone_pii`
  - `test_phone_at_start_of_text`

### Plan
1. Modify the `phone_us` regex in `PII_PATTERNS` so the separator between number segments also accepts a space (e.g., broaden `[-.]?` to allow whitespace), letting `(555) 123-4567` match.
2. Run `pytest tests/unit/test_pii_scrubber.py -q` and confirm the four target tests now pass.
3. Confirm no regressions — verify the 20 previously passing tests still pass and the current formats (`555-123-4567`, `555.123.4567`) still work properly.
4. Manually re-run the reproduction snippet from the issue for `scrub()` and `detect()` to confirm both now handle the parenthesized format.

### Inputs & outputs
- **Input:** 
A text string passed to `scrub(text)` or `detect(text)` containing a US phone number in parenthesized format, e.g. `"Call me at (555) 123-4567"`.

- **Output change:**
`scrub()` returns the string with the number replaced by `[REDACTED]`; `detect()` returns a list containing a dict with `type="phone_us"` and the matched value/positions. Only the regex string in `PII_PATTERNS` will change.

### Risks & unknowns
- **Over-matching risk:**
Broadening the separator to allow whitespace could make the `phone_us` pattern match across line breaks or link two unrelated numbers together. I need to allow a literal space without matching newlines.

- **Interaction with `phone_intl`:**
Both `phone_us` and `phone_intl` run in `scrub()`/`detect()`. I should confirm my change doesn't create double matches or shift positions for the `+1 555 123 4567` case.

- **Out-of-scope note:**
A fifth test, `test_mixed_pii_and_text`, also fails, but it's caused by a separate over-redaction bug in the `street_address` pattern, not the phone pattern, so I will not address it here.

### Edge cases
- `(555) 123-4567` — parenthesized with a space (the primary target). Must redact.
- `(555)123-4567` — parenthesized with **no** space after the paren. Should still redact.
- `555-123-4567` and `555.123.4567` — existing dashed/dotted formats. Must remain redacted (no regression).
- A number at the very start of a string, e.g. `"(555) 123-4567 is my number."`. Must redact (this is `test_phone_at_start_of_text`).