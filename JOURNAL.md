## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The phone-number regex in `pii_scrubber.py` only matches dashed formats like
555-123-4567, so parenthesized formats like (555) 123-4567 — one of the most
common ways US phone numbers are written — pass through `scrub()` completely
unredacted, and `detect()` reports no PII found at all for that format. This
is a gap in the safety/PII-redaction layer of the app. Four existing unit
tests already cover this case and are currently failing. A successful fix
extends the phone-number pattern matching to also catch the parenthesized
format, so both `scrub()` and `detect()` correctly identify and redact it,
and the four related tests pass.

**Selection reasoning:** I chose this as a Tier 1 issue since it's my first
time contributing to an unfamiliar multi-module codebase. The bug is
isolated to a single function in one file, has clear reproduction steps
and four named failing tests to validate against, so I can verify
correctness without needing to understand the rest of the app's
architecture.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
