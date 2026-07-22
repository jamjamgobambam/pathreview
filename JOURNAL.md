## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `phone_us` regex pattern in `safety/pii_scrubber.py` failed to match phone
numbers in parenthesized format like `(555) 123-4567`. The bug was caused by
a word boundary (`\b`) placed directly before the optional opening parenthesis,
which never matches since `(` is not a word character. This meant `scrub()`
left parenthesized numbers unredacted and `detect()` reported no PII for them,
while dashed formats like `555-123-4567` worked fine. The fix moves the word
boundary to sit before the digit group itself and allows whitespace as a
separator so formats like `+1 555 123 4567` are also supported.

**Branch name:** fix/146-parenthesized-us-phone-pii

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
