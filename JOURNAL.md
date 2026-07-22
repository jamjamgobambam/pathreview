# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` uses a regular expression to find and
redact US phone numbers. That regex only recognizes the dashed format, like
`555-123-4567`. It misses the parenthesized area code format, like
`(555) 123-4567`, even though that's a very common way people write phone
numbers. Because of this, `scrub()` leaves parenthesized numbers untouched in
the output text, and `detect()` reports no PII found when a parenthesized
number is present in the input. That's a false negative in a component whose
whole job is catching this kind of data. A correct fix updates the phone number
pattern so it matches both formats, which should make the existing failing
tests pass: `test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, and `test_phone_at_start_of_text`.

**Branch name:** fix/146-parenthesized-phone-regex

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
