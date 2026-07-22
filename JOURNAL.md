# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The safety layer's PII scrubber (`safety/pii_scrubber.py`) is supposed to catch
and redact personal information, including US phone numbers, before text is
stored or displayed. Its `phone_us` regex only allows `-` or `.` between the
number groups, so a common format like `(555) 123-4567` — where a space follows
the closing parenthesis — is never matched and passes through unredacted. This
is a real privacy leak, since a phone number a user expects to be hidden stays
visible. A successful fix updates the regex to also accept a space (and the
parenthesized area-code form) as a valid separator, adds a test covering that
format, and leaves the existing phone/email/SSN cases still passing.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
