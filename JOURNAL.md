## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber's phone-number regex in `safety/pii_scrubber.py` matches
dashed formats like `555-123-4567` but misses parenthesized formats like
`(555) 123-4567`, because the pattern allows an optional closing paren but
no whitespace after it before the next digit group. As a result, `scrub()`
leaves parenthesized phone numbers in the output unredacted and `detect()`
fails to flag them as PII at all — a real privacy gap since parenthesized
format is one of the most common ways US phone numbers are written. A
correct fix updates the `phone_us` pattern to tolerate the space (or other
separator) after the area code parenthesis, and should be validated against
the existing `test_us_phone_number_redaction` test.

**Branch name:** fix/146-pii-scrubber-parenthesized-phone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bimalitani100/pathreview/commit/106cb12df5fcac6fe088e5a16514e3df1d177f95

**Reproduction summary:** Ran the scrub()/detect() snippets from issue #146 locally — confirmed `(555) 123-4567` passes through scrub() unredacted while `555-123-4567` in the same string is correctly redacted, and detect() returns [] for the parenthesized number. Confirmed via pytest that 4 of 6 phone-related tests fail (test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text); the other 2 (international, phone-at-end) pass.

**PLAN.md link:** https://github.com/bimalitani100/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** [optional]

**Blockers or open questions:**
Unclear whether "+1 555 123 4567" (space-separated international-style format) needs a separate fix beyond the parenthesis issue — will check when implementing next week.