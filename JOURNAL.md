## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The test suite for `review_service.py` is experiencing widespread failures where 13 out of 19 total tests are completely broken. Currently, the database mock sessions are improperly returning asynchronous coroutine objects instead of synchronous result mocks when `result.scalars()` is called, causing downstream chained methods like `.first()` and `.all()` to throw an AttributeError. A successful fix will correctly restructure these test fixtures using a combination of AsyncMock and MagicMock so that the existing CRUD tests can execute cleanly and unblock the test suite runner.

**Branch name:** fix/158-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection Notes & Scope Reasoning:

I evaluated this issue against the "Is this right for me?" checklist. While navigating a new multi-module project can be complex, this Tier 1 issue is highly scoped specifically to the `tests/unit/test_review_service.py` file, meaning it does not introduce architectural risk or require cross-module refactoring. Fixing a broken test suite provides immediate, high-impact value to the development pipeline without risking production regressions, making it the perfect scope fit for my current comfort level with the codebase.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/WenAlgo998/pathreview/commit/cb2668a6e3ad9f5a5b0277bd2c655fd83318242d

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py -q` in my local environment and observed 13 test failures and 6 passes, reproducing `AttributeError: 'coroutine' object has no attribute 'first'` caused by misconfigured async mocks.

**PLAN.md link:** https://github.com/WenAlgo998/pathreview/blob/fix/158-async-mocks/PLAN.md

**Blockers or open questions:**
None at this time. The issue is fully isolated to mock setup within `tests/unit/test_review_service.py`.
