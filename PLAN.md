## Solution plan

**Issue:** [#146: PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand

`PIIScrubber` uses the shared `phone_us` regular expression for both `scrub()` and `detect()`. The current pattern handles formats such as `555-123-4567`, but its leading `\b` cannot begin a match before `(` because both the opening parenthesis and the preceding start-of-text or whitespace position are non-word boundaries. The separator portions also accept only hyphens and periods, so they do not allow the space after a closing parenthesis or the spaces in `+1 555 123 4567`.

As a result, `scrub()` leaves `(555) 123-4567` unchanged and `detect()` returns no phone PII for the same value. The expected behavior is for the scrubber to recognize the complete phone number, replace it with one `[REDACTED]` marker, and report a `phone_us` detection whose value and offsets cover the full original number.

This is a focused pattern and regression-test change. The public behavior of `PIIScrubber`, the replacement marker, and patterns for email, international phone numbers, SSNs, and street addresses are outside the implementation scope.

### Map

- `safety/pii_scrubber.py`
  - Replace the leading and trailing word-boundary assumptions in `phone_us` with boundaries that work when a number starts with `(` or `+1`.
  - Allow the supported separators between country code, area code, exchange, and subscriber number: spaces, hyphens, and periods.
  - Require parentheses around the area code to be balanced while retaining the existing unparenthesized formats.
  - Keep one shared pattern so `scrub()` and `detect()` remain consistent.
- `tests/unit/test_pii_scrubber.py`
  - Use the existing failing tests for parenthesized redaction, supported US formats, phone detection, and a phone number at the start of text as the primary regression coverage.
  - Strengthen assertions where needed to verify that the full parenthesized number is removed and that `detect()` returns the complete value with accurate start and end offsets.
  - Add focused boundary cases if they are not already covered, including punctuation-adjacent numbers and avoiding matches inside longer alphanumeric text.
- `JOURNAL.md`
  - Record the Issue #146 implementation and the final before-and-after test results when the code change is completed.

### Plan

1. **Confirm the failing baseline.** Run the direct `scrub()` and `detect()` reproduction with `(555) 123-4567`, then run `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text` to record the current four failures.
2. **Define the matching contract.** Treat `555-123-4567`, `(555) 123-4567`, `555.123.4567`, `+1 555 123 4567`, and the existing compact form as valid US phone inputs. Require a complete match with balanced optional area-code parentheses and boundaries that do not consume surrounding text.
3. **Update the shared US phone pattern.** Revise only `PII_PATTERNS["phone_us"]` so it accepts parenthesized area codes and supported separators while preserving the full match for replacement and detection offsets.
4. **Complete regression coverage.** Verify that `scrub()` emits exactly one `[REDACTED]` marker for one phone number, that no digits or parentheses from the matched phone remain, and that `detect()` reports `type="phone_us"`, the full original value, and correct offsets. Add narrow negative cases to guard against embedded partial matches or unbalanced parentheses.
5. **Validate the result.** Re-run the direct reproduction, the four issue-specific tests, the complete PII scrubber test module, and the repository's unit and quality checks. Record the verified commands and results in `JOURNAL.md`.

The implementation should remain limited to the US phone pattern and its tests unless validation reveals a direct conflict with another PII pattern.

### Inputs & outputs

**Inputs**

- Text containing a parenthesized US phone number, including `(555) 123-4567` at the start, middle, or end of text.
- Existing supported US formats: `555-123-4567`, `555.123.4567`, `+1 555 123 4567`, and a compact ten-digit number.
- Surrounding punctuation or ordinary text used to verify that match boundaries are accurate.

**Outputs**

- `scrub("Call me at (555) 123-4567 or 555-123-4567")` returns `"Call me at [REDACTED] or [REDACTED]"`.
- `detect("Call me at (555) 123-4567")` includes one `phone_us` item with value `(555) 123-4567` and offsets that extract that exact substring.
- All previously supported US phone formats continue to be redacted and detected.
- Focused regression tests prevent the parenthesized format from silently passing through again.

### Risks & unknowns

- Broadening separators too far could match digit sequences split across lines or unrelated numeric data. Separator handling should be limited to the formats covered by the matching contract.
- Removing `\b` without replacement boundaries could allow a ten-digit substring inside a longer identifier to be redacted. Explicit non-word lookarounds or equivalent boundary logic should protect both ends.
- Making opening and closing parentheses independently optional would accept malformed values such as `(555 123-4567` or `555) 123-4567`. The area-code alternatives should enforce balanced parentheses.
- `detect()` runs every PII pattern independently, so the revised US pattern should be checked for overlap with `phone_intl`, especially for numbers beginning with `+1`.
- Existing assertions sometimes check only for the presence of `[REDACTED]`; those assertions may pass even if only part of a number is matched. Exact-value and offset checks are needed for this privacy-sensitive behavior.

### Edge cases

- A parenthesized number at index `0`, where no preceding character exists.
- A parenthesized number after whitespace or punctuation and at the end of text.
- Multiple phone numbers in one string, mixing parenthesized and dashed formats.
- A `+1` country code separated from the area code by a space, hyphen, period, or no separator where supported.
- Compact ten-digit numbers that were accepted by the previous pattern.
- Phone-like digits embedded in letters or in a longer digit sequence, which must not be partially matched.
- Unbalanced area-code parentheses, which must not be treated as a valid complete phone number.
- Empty text and text without PII, which must remain unchanged and produce no detections.

### Definition of done

- The direct reproduction redacts both `(555) 123-4567` and `555-123-4567` completely.
- Detection returns the full parenthesized phone number as `phone_us` with accurate start and end offsets.
- `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text` all pass.
- The complete `tests/unit/test_pii_scrubber.py` module and repository unit/quality checks pass without regressions in other PII types.
- Regression coverage includes complete-match assertions and relevant positive and negative boundary cases.
- The implementation changes only the files required for Issue #146, and `JOURNAL.md` records the verified outcome.
