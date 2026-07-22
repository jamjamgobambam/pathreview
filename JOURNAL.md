## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146
**Issue title:** PII scrubber fails to redact parenthesized US phone numbers
**Tier:** [x] Tier 1

**Problem summary:**
<!--
scaffold notes, replace with my own 3-5 sentences before submitting:
- broken: phone regex anchors on \b (word boundary), ( isn't a word char,
  so it never matches when a number opens with a parenthesized area code
  like (555) 123-4567. Dashed format 555-123-4567 still matches fine.
- effect: scrub() leaves those numbers in plaintext, detect() reports zero
  PII found even though a phone number is right there
- fix: broaden the regex to also match when the number opens with (,
  verified by 4 named failing tests in tests/unit/test_pii_scrubber.py
-->
[REPLACE THIS LINE WITH MY OWN WORDS]

**Branch name:** fix/146-pii-scrubber-parenthesized-phone
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger
