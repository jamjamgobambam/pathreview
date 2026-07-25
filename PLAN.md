## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers https://github.com/ascherj/pathreview/issues/146

### Understand
The root cause of this issue is the regex logic that doesn't work correctly for parenthesized or space-separated US phone numbers. Once it matches the parentheses and the first 3 digits inside them, it expects either a "-" or a "." and any number containing a space will cause this to fail. The expected behavior is that when `scrub()`/`detect()` receives a phone number like (555) 123-4567, it recognizes that as PII and the phone number text becomes "[REDACTED]". What actually happens is a silent return of 0 matches instead of a thrown error.

### Map
The two files to be touched are `safety/pii_scrubber.py` and `tests/unit/test_pii_scrubber.py`. Inside of `safety/pii_scrubber.py` I will only be touching line 15 which is inside of the `PII_PATTERNS` definition under the `class PIIScrubber`. Inside of `tests/unit/test_pii_scrubber.py` I will be adding one edge case "(555)123-4567, parenthesis with no space" to the `formats` list inside `test_us_phone_formats`.

### Plan
Step 1: Update the phone_us regex on line 15 changing all three `[-.]?` separator groups to `[-. ]?` so a space is accepted alongside dash and dot. 
Step 2: Add the new edge case to the tests: "(555)123-4567"
Step 3: Rerun `tests/unit/test_pii_scrubber.py` to confirm they pass and check for regressions

### Inputs & outputs
Input: A text string that contains arbitrary text and may contain a phone number anywhere inside of it
Output: `scrub()` returns a string with the matched phone number substring replaced by "[REDACTED]". `detect()` returns a list[dict] where each dict has type (e.g. `phone_us`), value (the matched text), and `start/end` (character positions).

### Risks & unknowns
- `test_mixed_pii_and_text` will still fail after my fix. It's caused by an unrelated bug in the street_address regex (line 18), not the phone regex I'm changing. I'm treating it as out of scope for #146, but flagging it here so a reviewer doesn't assume my change caused it.
- Broadening a regex may cause it to match things it shouldn't. It's possible that other number groupings found in a resume (like an ID number, a date, or stat) could flag the regex, especially after it also accepts a space after the numbers. I will rerun the full `test_pii_scrubber.py` file which would catch this if it happened.

### Edge cases
- Text without a phone number
- A phone number at the very start or end of a string
- The already working formats (555-123-4567, 555.123.4567, +1 555 123 4567) need to keep working exactly as before
- Malformed input with repeated/multiple separator characters (e.g. double spaces) is out of scope for #146.
