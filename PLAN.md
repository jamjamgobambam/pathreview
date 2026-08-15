# Solution Plan

**Issue:** [#146 - PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

**Working branch:** `fix/146-pii-parenthesized-phone`

## Understand

PathReview's safety layer uses `PIIScrubber` to remove personally identifiable information from text before that text is stored, reviewed, or sent through other parts of the system. The specific bug I am fixing is that US phone numbers written in the common parenthesized format, such as `(555) 123-4567`, are not redacted by `scrub()` and are not returned by `detect()`.

The expected behavior is that `(555) 123-4567` should be treated the same way as `555-123-4567`, `555.123.4567`, and `+1 555 123 4567`: the full phone number should be replaced with `[REDACTED]` by `scrub()`, and `detect()` should return a `phone_us` entry with the matched value and character positions.

The actual behavior is confirmed in `docs/repro-146.txt`: four phone-related unit tests currently fail. The failure happens because the current `phone_us` regex in `safety/pii_scrubber.py` only allows hyphens, dots, or no separator between the area code and prefix. It does not allow the space after the closing parenthesis in `(555) 123-4567`. A second issue is the leading `\b` word boundary, which cannot match immediately before `(` when the phone number starts at the beginning of the input.

## Map

The fix is intentionally small and should stay inside the PII scrubbing safety layer.

Likely files involved:

- `safety/pii_scrubber.py`: contains `PIIScrubber.PII_PATTERNS`, including the `phone_us` regex that needs to change.
- `tests/unit/test_pii_scrubber.py`: contains the failing tests that define the expected behavior for phone redaction and detection.
- `docs/repro-146.txt`: records the local reproduction output showing the issue exists on this branch before the fix.

Likely functions and data involved:

- `PIIScrubber.scrub(text: str) -> str`: takes raw text and returns text with PII replaced by `[REDACTED]`.
- `PIIScrubber.detect(text: str) -> list[dict]`: takes raw text and returns structured detections with `type`, `value`, `start`, and `end`.
- `PIIScrubber.PII_PATTERNS["phone_us"]`: the regex pattern used by both `scrub()` and `detect()` for US phone numbers.

I do not expect to touch the API layer, database layer, frontend, or the international phone regex.

## Plan

1. Re-run the focused phone tests from `tests/unit/test_pii_scrubber.py` to confirm the four failures in `docs/repro-146.txt` still reproduce locally.
2. Update only the `phone_us` pattern in `safety/pii_scrubber.py` so it accepts whitespace separators as well as hyphen and dot separators.
3. Adjust the leading boundary of the `phone_us` pattern so numbers that start with `(` can match, while preserving a trailing boundary after the final four digits.
4. Add focused regression tests in `tests/unit/test_pii_scrubber.py` for parenthesized formats that are easy to break later, including `(555) 123-4567` at the start of text and `(555)123-4567` without a space.
5. Run the focused PII scrubber test file, then run the broader unit/check commands required by the project to make sure the widened regex does not break existing PII behavior.
6. Commit the implementation separately in Week 9 using a conventional commit message such as `fix(safety): redact parenthesized US phone numbers`.

## Inputs & Outputs

The fix input is a string passed to `PIIScrubber.scrub()` or `PIIScrubber.detect()`. No public function signature should change.

Inputs that should be handled after the fix:

- `"Call me at (555) 123-4567"`
- `"(555) 123-4567 is my phone number."`
- `"Contact: (555)123-4567"`
- `"Contact: +1 555 123 4567"`
- `"Contact: 555-123-4567"`
- `"Contact: 555.123.4567"`

Expected `scrub()` output behavior:

- The complete phone number is replaced with `[REDACTED]`.
- Non-PII text around the phone number is preserved.
- Existing email, SSN, street address, and international phone behavior remains unchanged.

Expected `detect()` output behavior:

- A parenthesized US phone number returns at least one detection.
- The detection has `type == "phone_us"`.
- The detection's `value` is the full matched phone string, not just a partial group.
- The detection's `start` and `end` positions point to the phone number inside the original text.

## Risks & Unknowns

- **Risk in `safety/pii_scrubber.py`: over-matching longer digit strings.** If the leading boundary is relaxed too much, the regex could match inside unrelated numeric text. I will keep a trailing word boundary after the final four digits and add/verify tests for longer numeric runs.
- **Risk in `safety/pii_scrubber.py`: false positives with SSNs.** `phone_us` runs before `ssn` because both patterns live in the same ordered `PII_PATTERNS` dictionary. The phone pattern must keep a strict `3-3-4` shape so it does not consume SSNs like `123-45-6789`, which are `3-2-4`.
- **Risk in `tests/unit/test_pii_scrubber.py`: tests may be too permissive.** Some existing assertions only check whether `[REDACTED]` appears. I will add focused tests that also assert the original phone number is gone and detection returns the full value.
- **Unknown in `phone_intl`: overlap with `+1` formats.** The `phone_intl` pattern is separate and should remain untouched. I will verify existing international-phone tests still pass after changing only `phone_us`.
- **Unknown in project-wide checks:** the regex change is small, but `make check` may reveal formatting or type issues unrelated to this file. If unrelated existing failures appear, I will document them separately rather than mixing them into this fix.

## Edge Cases

The fix must handle these concrete cases gracefully:

- Parenthesized number in the middle of text: `"Call me at (555) 123-4567 after 5."`
- Parenthesized number at the very start of text: `"(555) 123-4567 is my number."`
- Parenthesized number with no space after the area code: `"Use (555)123-4567 instead."`
- Space-separated country-code format: `"Use +1 555 123 4567 for the US office."`
- Already-supported dashed format: `"Use 555-123-4567."`
- Already-supported dotted format: `"Use 555.123.4567."`
- SSN-shaped input that must not become a phone match: `"SSN: 123-45-6789."`
- Version-number text that must not be detected as PII: `"The project uses version 1.2.3."`
- Long digit runs that should not be partially redacted as a phone number: `"Tracking id 5551234567890 was generated."`

## Definition of Done

The plan will be ready for Week 9 implementation when:

- The local reproduction is committed in `docs/repro-146.txt`.
- This `PLAN.md` is committed on `fix/146-pii-parenthesized-phone`.
- `JOURNAL.md` links both the reproduction commit and this plan.
- The planned fix is limited to `safety/pii_scrubber.py` plus focused tests in `tests/unit/test_pii_scrubber.py`.
