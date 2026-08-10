# PLAN

# Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers  
**Issue Link:** https://github.com/ascherj/pathreview/issues/146

---

## Understand

This issue affects the safety layer of the application, specifically the PII scrubber responsible for detecting and redacting personally identifiable information. The current implementation is intended to detect several US phone number formats, but numbers written with parentheses around the area code, such as `(415) 555-1234`, are not consistently detected and therefore are not redacted. The expected behavior is for these phone numbers to be replaced with `[REDACTED]` while maintaining support for all currently supported phone number formats.

---

## Map

The primary files involved are:

- `safety/pii_scrubber.py`
  - Contains the `PIIScrubber` class.
  - Defines the `phone_us` regular expression.
  - Implements the `scrub()` and `detect()` methods.

- `tests/unit/test_pii_scrubber.py`
  - Contains unit tests for phone-number detection and redaction.
  - Will be used to verify that parenthesized phone numbers are correctly handled.

---

## Plan

1. Review the current `phone_us` regular expression in `safety/pii_scrubber.py`.
2. Reproduce the issue using the existing unit tests and confirm the current behavior.
3. Update the regular expression so that phone numbers with parenthesized area codes are detected correctly.
4. Verify that existing supported phone number formats continue to pass.
5. Run the relevant unit tests and confirm that no regressions have been introduced.

---

## Inputs & outputs

### Input

```
Please call me at (415) 555-1234.
```

### Current Output

```
Please call me at (415) 555-1234.
```

### Expected Output

```
Please call me at [REDACTED].
```

The `detect()` method should also return a detection of type `phone_us` for the phone number.

---

## Risks & unknowns

- Updating the regular expression could accidentally affect detection of other supported phone number formats.
- A broader regex may introduce false positives by matching numeric strings that are not phone numbers.
- The interaction between the US phone pattern and the international phone pattern should be verified to avoid overlapping matches.
- Additional edge cases may already exist in the test suite that need to continue passing after the change.

---

## Edge cases

The updated solution should correctly handle:

- `(415) 555-1234`
- `(415)555-1234`
- `(415)-555-1234`
- `415-555-1234`
- `415.555.1234`
- `+1 (415) 555-1234`
- Multiple phone numbers within the same document.
- Phone numbers surrounded by punctuation.
- Existing supported phone number formats should continue to work without modification.
- Numeric strings that are not valid phone numbers should not be falsely redacted.