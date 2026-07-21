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