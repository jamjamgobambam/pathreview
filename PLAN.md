## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand

The `phone_us` regex in `PIIScrubber.PII_PATTERNS` (`safety/pii_scrubber.py`, line 15) uses `\b` as its leading anchor. `\b` matches at the boundary between a word character (`[a-zA-Z0-9_]`) and a non-word character. When a phone number begins with `(`, the character before the opening paren is typically a space — both the space and the `(` are non-word characters, so no word boundary exists and the regex never matches. Separately, the separator group `[-.]?` between digit clusters does not allow for a space, so the standard `(555) 555-1234` format (closing paren followed by a space before the exchange) also fails to match independently of the anchor problem.

**Expected:** `(555) 555-1234` is replaced with `[REDACTED]` in both `scrub()` and `detect()`.

**Actual:** The parenthesized format passes through unchanged; only bare formats like `555-123-4567` are caught.

### Map

| File | Role |
|---|---|
| `safety/pii_scrubber.py` | Contains `PIIScrubber.PII_PATTERNS["phone_us"]` — the regex to fix (line 15) |
| `tests/unit/test_pii_scrubber.py` | Unit tests for `PIIScrubber` — reproduction tests added here, passing tests verified here after the fix |

No other files need to change. The `scrub()` and `detect()` methods themselves iterate over `PII_PATTERNS` generically, so fixing the pattern is sufficient.

### Plan

1. **Add failing reproduction tests** (already done in this branch): four targeted tests in `tests/unit/test_pii_scrubber.py` that each assert `[REDACTED]` appears and the original `(NXX) NXX-XXXX` string does not — these fail before the fix and pass after it.

2. **Fix the leading anchor** in `pii_scrubber.py`: replace the leading `\b` with `(?<!\d)` (a negative lookbehind asserting the character before the match is not a digit). This prevents matching phone-like sequences embedded inside longer digit strings while correctly allowing `(` — or any non-digit — to precede the match.

3. **Widen the area-code-to-exchange separator**: change the first `[-.]?` (between the area code and exchange groups) to `[-.\s]?` so a space after the closing `)` is accepted.

4. **Run the full test suite** to confirm the four reproduction tests now pass and no existing tests regress: `python -m pytest tests/unit/test_pii_scrubber.py -v`.

5. **Verify no false positives**: manually confirm that digit strings embedded in longer numbers (e.g., a 15-digit account number containing a 10-digit substring) are not incorrectly matched, by adding or reviewing the `test_detect_no_false_positives` test.

### Inputs & outputs

**Input:** Any string passed to `PIIScrubber.scrub()` or `PIIScrubber.detect()` that contains a US phone number in parenthesized format — e.g., `"Call (555) 555-1234"`, `"(555)555-1234 is the number"`, `"+1 (555) 555-1234"`.

**Output:**
- `scrub()` returns the same string with the phone number substring replaced by `[REDACTED]`.
- `detect()` returns a list entry with `type="phone_us"`, the matched `value`, and accurate `start`/`end` positions.

The single-character change to the regex (`\b` → `(?<!\d)`, `[-.]?` → `[-.\s]?`) is the only code change required; no method signatures or API surfaces change.

### Risks & unknowns

- **False positives from removing `\b`:** The trailing `\b` at the end of the regex could also fail for numbers followed by non-word characters (e.g., a closing paren or punctuation). It should be audited too — replacing it with `(?!\d)` (negative lookahead, not a digit) is likely safer.
- **Overlapping match with `phone_intl`:** The pattern `+1 (555) 555-1234` could be partially matched by both `phone_us` and `phone_intl`. This is likely harmless (both would produce `[REDACTED]`) but worth confirming the output isn't double-tagged.
- **`[-.\s]?` greediness:** Allowing `\s` as a separator means `555 1234567` (two tokens separated by a single space) could be matched if surrounded by the right context. Need to confirm this doesn't produce unexpected redaction on number-heavy text.

### Edge cases

| Input | Expected output |
|---|---|
| `"(555) 555-1234"` mid-sentence | `[REDACTED]` |
| `"(555) 555-1234"` at start of string | `[REDACTED]` |
| `"(555)555-1234"` — no space after paren | `[REDACTED]` |
| `"+1 (555) 555-1234"` — with country code | `[REDACTED]` |
| `"555-123-4567"` — existing bare format | still `[REDACTED]` (no regression) |
| `"555.123.4567"` — dot separator | still `[REDACTED]` (no regression) |
| `"The ID is 15551234567890"` — 10-digit subsequence in longer number | not redacted (no false positive) |
| Empty string `""` | `""` unchanged |
