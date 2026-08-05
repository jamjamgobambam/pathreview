## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [X] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The issue is in the README scoring unit test, where the test data is inconsistent with the expectations it sets. The fixture used by the README scorer test is too short to satisfy the assertion that the scored README should be considered “comprehensive,” so the test fails even though the scorer may be behaving correctly. A successful fix would make the fixture or the assertion match the intended test behavior, so the unit test accurately validates the README scorer’s output.

**Branch name:** fix/156-README-test-fixture-too-short

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/bluecrushangel/pathreview/commit/98ab411949763b24dacf4d1cab1c2c8f21775276)

**Reproduction summary:**
I reproduced the issue by running the testscript:
pytest tests/unit/test_readme_scorer.py -q 

I checked the error logs and verified the issue exists.

**PLAN.md link:** (https://github.com/bluecrushangel/pathreview/blob/fix/156-README-test-fixture-too-short/PLAN.md)
**Walkthrough video (recommended):** N/A 

**Blockers or open questions:**
N/A

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix by expanding the `test_readme_scorer.py` fixture so the sample README now exceeds the comprehensive word-count threshold and validates the intended category.

**Next steps:**
Finalize the PR description, verify the test passes, and prepare the branch for submission.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/893)

**Branch:** (https://github.com/bluecrushangel/pathreview/tree/fix/156-README-test-fixture-too-short)

**What you built:**
The readme_scorer unit test fixture was too short to meet its own comprehensive word-count assertion. I expanded the sample README in test_readme_scorer.py so it now exceeds the scorer’s > 500 word threshold and validates the intended "comprehensive" category.

**Tests added or updated:**
Updated test_readme_scorer.py to expand the fixture and validate that the README sample now exceeds the comprehensive word-count threshold and returns word_count_category == "comprehensive".

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** "none"