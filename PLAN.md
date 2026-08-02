# PLAN.md - Issue #146

## Issue
PII scrubber fails to redact and detect parenthesized US phone numbers such as (555) 123-4567.

## Goal
Update US phone matching so both scrub() and detect() correctly handle common US formats, including parenthesized area codes, without regressing existing behavior.

## Reproduction status
Confirmed locally with the PIIScrubber snippet:
- scrub("Call me at (555) 123-4567 or 555-123-4567") leaves the parenthesized number unredacted.
- detect("Call me at (555) 123-4567") returns an empty list.

## Root-cause hypothesis
The current phone_us regex in safety/pii_scrubber.py does not consistently match numbers that begin with a parenthesized area code, especially with surrounding boundary/spacing conditions.

## Implementation plan
1. Update the phone_us regex in safety/pii_scrubber.py to support:
   - (555) 123-4567
   - (555)123-4567
   - 555-123-4567
   - Optional leading country code (+1 or 1) where already intended.
2. Keep the scope focused to phone_us pattern logic only.
3. Verify scrub() redaction output for mixed-format inputs.
4. Verify detect() returns phone_us entries with correct value/start/end fields.

## Validation plan
1. Run targeted tests:
   - test_us_phone_number_redaction
   - test_us_phone_formats
   - test_detect_phone_pii
   - test_phone_at_start_of_text
2. Run the full file for regression coverage:
   - tests/unit/test_pii_scrubber.py
3. Re-run manual snippet to confirm expected redaction/detection behavior.

## Risks and mitigations
- Risk: Overly broad regex may create false positives.
  - Mitigation: Keep separators and digit grouping strict (3-3-4), validate with existing tests.
- Risk: Pattern changes could break current dashed format support.
  - Mitigation: Preserve existing supported formats and include targeted assertions.

## Definition of done
- Parenthesized US phone numbers are redacted by scrub().
- Parenthesized US phone numbers are detected by detect().
- The four targeted tests pass.
- No regressions in tests/unit/test_pii_scrubber.py.
