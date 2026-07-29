## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The phone number regex in pii_scrubber.py only detects dashed formats (e.g., 555-123-4567), leaving parenthesized numbers like (555) 123-4567 unredacted. Consequently, scrub() misses standard US numbers while detect() returns an empty array instead of flagging the PII. This issue causes several unit tests in tests/unit/test_pii_scrubber.py to fail, including test_us_phone_number_redaction and test_detect_phone_pii. Updating the matching pattern to support parenthesized area codes will resolve the leakage.

**Branch name:** docs/146-pii-scrubber-fail

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
I reproduced the issue by adding the parenthesized phone number format (555) 123-4567 to the inputs in tests/unit/test_pii_scrubber.py. When running the tests, I observed that the scrub() method left the number unredacted and detect() failed to identify it as PII, causing the tests to fail as expected.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]