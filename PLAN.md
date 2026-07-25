# Solution Plan

**Issue:** https://github.com/ascherj/pathreview/issues/146

## Understand
The PII scrubber is failing to redact parenthesized U.S. phone number formats (e.g., `(123) 456-7890`). This leaves sensitive user information exposed because the current regular expression patterns in `PII_PATTERNS` do not account for optional or required parenthesis wrappers around the area code, occasionally misinterpreting them or missing them entirely.

## Map
- **Module/File:** `pii_scrubber.py`
- **Specific Components:** 
  - The `PII_PATTERNS` dictionary containing the regular expression definitions.
  - The `PIIScrubber().scrub()` method which iterates through patterns to sanitize text.
- **Test File:** `tests/test_pii_scrubber.py` for adding regression tests.

## Plan
1. Update the U.S. phone number regex pattern inside the `PII_PATTERNS` dictionary in `pii_scrubber.py` to correctly capture parenthesized area code formats. Also updating other regex patterns if needed.

2. Implement new unit test functions inside `tests/test_pii_scrubber.py` targeting parenthesized phone numbers alongside standard formats.

3. Run `pytest` locally to verify that the new test cases pass successfully and that no regressions are introduced in existing PII tests.

## Inputs & outputs

- **Input:** Raw text strings containing sensitive data with parenthesized U.S. phone numbers (e.g., `User can be reached at (555) 123-4567`).

- **Output:** Sanitized text string with parenthesized phone numbers replaced by the standard redaction token (e.g., `User can be reached at [REDACTED]`).

## Risks & unknowns
- **Risk:** Modifying the regex pattern inside `PII_PATTERNS` in `pii_scrubber.py` might introduce false positives, accidentally matching non-phone parenthesized content (such as legal references or shorthand formatting). This will need to be checked against existing test cases.

## Edge cases

1. **Empty or Null Strings:** Empty string input must be handled gracefully with an early return for performance without slowing the program or throwing unexpected errors.

2. **Compact Parenthesized Numbers:** Phone numbers formatted with parentheses but missing the standard space after the closing parenthesis (e.g., `(555)123-4567`) must still be scrubbed correctly.