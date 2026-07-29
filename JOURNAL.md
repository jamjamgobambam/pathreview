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
## Week 8 — Reproduction & solution planning
**Reproduction commit link:** https://github.com/pclerveau2025/pathreview/commit/76eb5e2
**Reproduction summary:**
Reproduced the bug by testing the phone_us regex against parenthesized US phone numbers such as (555) 123-4567. Confirmed the word boundary placement before the optional parenthesis prevented a match, so the scrubber left the number unredacted while dashed formats worked correctly.
**PLAN.md link:** https://github.com/pclerveau2025/pathreview/blob/fix/146-parenthesized-us-phone-pii/PLAN.md
**Walkthrough video (recommended):** [none recorded]
**Blockers or open questions:**
None currently. Still need to verify no overlap/duplicate detection occurs between phone_us and phone_intl patterns once the fix is applied more broadly.