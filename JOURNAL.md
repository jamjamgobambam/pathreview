## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Why this tier:** Chose Tier 1 as my first contribution to a large codebase — the fix is contained to one regex in one file with pre-written tests, a realistic scope for a two-week window.

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` uses one regex to find phone numbers, but it only allows dashes or dots between digit groups so parenthesized numbers like (555) 123-4567 don't match and slip through un-redacted, with `detect()` reporting no PII. A successful fix widens the pattern to catch parenthesized and space-separated formats without breaking the dashed/dotted ones already handled, making the four failing tests in `tests/unit/test_pii_scrubber.py` pass.

**Branch name:** fix/146-parenthesized-phone-number-error

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger