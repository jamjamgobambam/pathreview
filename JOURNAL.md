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

**PLAN.md link:** [commit link](https://github.com/paolitacute/pathreview/commit/0f7b1a3c666a8de0321fd8ad53499ddf208847ff)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
I implemented the regex fix for the PII scrubber to correctly identify US phone numbers with parenthesized area codes. I updated the `phone_us` pattern and resolved the Ruff linter line-length errors.

**Next steps:**
Write a new test for mixed spacing, ensure all existing unit tests pass, and open the pull request.

**Blockers:**
None.

### Check-in 2 (end of week)
**PR link:** [PR Link](https://github.com/ascherj/pathreview/pull/900#issue-5066724071)
**Branch:** 146 pii scrubber fail
**What you built:**
I modified the `phone_us` regex pattern in `pii_scrubber.py` to allow for optional parentheses and spaces around the area code. This ensures phone numbers formatted like `(555) 123-4567` are successfully caught and redacted by the scrubber.

**Tests added or updated:**
None applicable.

**Self-review confirmation:** (x) make check passes (x) make test-unit passes
**Draft PR feedback received from:** None
