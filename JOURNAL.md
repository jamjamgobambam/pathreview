## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/158](https://github.com/ascherj/pathreview/issues/158)

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The unit tests for the `review_service` currently fail because they incorrectly use `AsyncMock` for synchronous database result objects. Specifically, when the tests mock `db.execute()`, they return an `AsyncMock`. This raises an `AttributeError` in the service code. A successful fix will update the test setup in `tests/unit/test_review_service.py` to use a regular `Mock` or `MagicMock` for the query result object. This will correctly simulate the synchronous behavior of SQLAlchemy's query results, allowing all 19 tests to pass.

**Branch name:** [fix/158-review-service-async-mocks]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is This Issue Right For Me?" checklist**
[x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
[x] I've located the relevant files and confirmed they exist in the codebase (tests/unit/test_review_service.py).
[x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after. (Before: Running pytest tests/unit/test_review_service.py throws 13 AttributeError failures. After: Running the same command will show 19 passing tests in green.)
[x] I have confirmed that the repository runs locally at localhost:5173.
[x] This is my first open source contribution: I'm choosing Tier 1.
[x] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.
[x] I've found and read the specific code the issue references (not just the file — the function or section).
[x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.I've found the test file for my module and read at least one test end-to-end.
[x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
[x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
[x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/mmicat/pathreview/commit/a6e797a

**Reproduction summary:**
I ran pytest tests/unit/test_review_service.py -q in the activated virtual environment. I observed 13 out of 19 tests failing with an AttributeError: 'coroutine' object has no attribute 'first', confirming that the AsyncMock configuration is causing the query results to incorrectly evaluate as coroutines.

**PLAN.md link:** https://github.com/mmicat/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've implemented the fix by changing AsyncMock to MagicMock for the query results in tests/unit/test_review_service.py. I also updated the assertion in test_list_reviews_ordered_by_created_at to check for two calls instead of one. I've tested and confirmed that all 19 tests pass!

**Next steps:**
Submit PR for review

**Blockers:**
N/A

---

### Check-in 2 (end of week; done early)

**PR link:** [https://github.com/ascherj/pathreview/pull/432](https://github.com/ascherj/pathreview/pull/432)

**Branch:** fix/158-review-service-async-mocks

**What you built:**
I fixed the review service unit tests by replacing `AsyncMock` with `MagicMock` for the mocked database query results. This ensures that the mocked objects correctly simulate the synchronous behavior of SQLAlchemy's `execute().scalars().first()`, preventing the coroutine `AttributeError`s that were causing the tests to fail. I also corrected the pagination test to expect two database calls instead of one.

**Tests added or updated:**
I updated `tests/unit/test_review_service.py`. I modified the mock configurations for 13 failing tests in this file so they properly return synchronous database result objects. All 19 tests in the file now pass.

**Self-review confirmation:** All 19 tests in review service pass. make check and make test-unit have pre-existing failures which I have documented.[x] make check passes [x] make test-unit passes

**Draft PR feedback received from:**
