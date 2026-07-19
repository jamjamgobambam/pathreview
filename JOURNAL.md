## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber can redact common phone-number formats, but it does not correctly detect US phone numbers that use parentheses around the area code. For example, a number such as `(555) 123-4567` may remain visible instead of being replaced. The problem appears to affect the phone-number pattern in `safety/pii_scrubber.py`. A successful fix will redact parenthesized phone numbers while keeping the currently supported formats working.

**Selection notes — Is this issue right for me?**
This issue has a focused scope and points to one main area of the codebase. It provides a clear example of the broken behavior and specific tests that can verify the solution. It is a Tier 1 issue, so it is appropriate for my current experience with contributing to a larger codebase. The issue should be manageable without requiring major architectural changes.

**Branch name:** `fix/146-parenthesized-phone-redaction`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger