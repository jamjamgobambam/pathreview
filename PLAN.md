## Solution plan

**Issue:** #146 - Parenthesized US phone numbers not detected by PII scrubber
https://github.com/pclerveau2025/pathreview/issues/146

### Understand
The phone_us regex placed the word boundary marker before the optional country code and parenthesis group. A word boundary only matches between a word character and a non-word character. When a phone number was preceded by whitespace or appeared after other non-word characters, there was no valid boundary at that position (since an open parenthesis is also a non-word character), so the regex failed to match numbers like (555) 123-4567. Expected behavior: any US phone number format, including parenthesized ones, should be detected and redacted. Actual behavior: parenthesized numbers were silently skipped, leaking PII.

### Map
- pii_scrubber.py (or wherever PIIScrubber.PII_PATTERNS lives) — contains the phone_us regex pattern
- Detection loop in the same file that calls re.finditer over PII_PATTERNS
- Any test file covering PII scrubbing (e.g. test_pii_scrubber.py) — needed to add a regression test

### Plan
1. Identify the exact failure case by writing a quick reproduction script/test with a parenthesized phone number embedded in text
2. Move the word boundary to sit directly before the digit group instead of before the optional prefix
3. Add whitespace as an accepted separator alongside dash and period, to support numbers like 555 123 4567
4. Add/update unit tests covering: parenthesized numbers, space-separated numbers, numbers preceded by punctuation or at start of string
5. Run the full test suite to confirm no regressions in email/SSN/address detection

### Inputs & outputs
- Input: raw text strings potentially containing PII (phone numbers in various formats: parenthesized, dash-separated, dot-separated, space-separated)
- Output: a list of detected PII matches (type, value, start, end offsets) used to redact/mask the original text

### Risks & unknowns
- Risk: loosening the regex could cause false positives (matching non-phone-number digit sequences of the same length)
- Risk: changes to phone_us could overlap with phone_intl pattern matching the same substring, causing duplicate detections
- Unknown: whether other PII types (address, SSN) have similar boundary placement bugs that haven't surfaced yet

### Edge cases
- Phone number at the very start of a string (no preceding character)
- Phone number immediately following punctuation, e.g. "Call:(555) 123-4567"
- Multiple phone numbers in the same string, some parenthesized and some not
- Phone number with mixed separators, e.g. "(555)123.4567"