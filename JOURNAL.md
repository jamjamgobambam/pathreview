## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` is supposed to find and redact
personal info like phone numbers, but its phone-number regex only matches
dashed formats such as `555-123-4567`. It misses the very common parenthesized
format `(555) 123-4567`, because the pattern doesn't allow the `)` plus a space
after the area code. As a result, `scrub()` leaves those numbers in the text and
`detect()` reports no PII for them, so real phone numbers can leak through. A
successful fix updates the regex so both formats are caught, making the four
related unit tests in `tests/unit/test_pii_scrubber.py` pass.

**Branch name:** fix/146-pii-parenthesized-phone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes (Is this right for me?):**
Good fit for a first contribution. It's a single-file change in
`safety/pii_scrubber.py`, the fix is a focused regex update, and the expected
behavior is already pinned down by existing failing tests, so I know exactly
what "done" looks like. No new dependencies, no cross-module changes, and it
runs with the default mock LLM (no API key needed). Scope is small and
self-contained.
