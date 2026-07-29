## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The safety layer’s phone-number pattern in `safety/pii_scrubber.py` redacts dashed US phone formats, but the parenthesized format `(555) 123-4567` slips through both `scrub()` and `detect()`. That means a common phone-number form can remain visible in user-facing output and escape PII detection entirely. A correct fix should expand the phone regex so the parenthesized format is matched and redacted consistently without breaking the existing phone redaction cases.

**Branch name:** fix/146-parenthesized-us-phone-numbers

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes:**
I can explain the issue in my own words without rereading the tracker: the scrubber misses a very common US phone format, so one PII path is inconsistent between detection and redaction. The relevant code is localized to `safety/pii_scrubber.py`, and the existing tests in `tests/unit/test_pii_scrubber.py` already cover the affected behavior, so this is a realistic Tier 1 fix. I also confirmed there are no blockers or dependencies listed on the issue.