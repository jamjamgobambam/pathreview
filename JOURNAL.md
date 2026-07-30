# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

`tests/unit/test_review_service.py` mocks the SQLAlchemy async `Result` object (`mock_result`) as an `AsyncMock`,
but in the real async API only `db.execute(...)` is awaited where the `Result` it returns is synchronous, so `.scalars()`, `.first()`,
and `.all()` are plain sync calls. Because `mock_result` is fully async,
calling `mock_result.scalars()` returns an unawaited coroutine instead of the configured mock,
so the service's `result.scalars().first()` / `.all()` chains raise `AttributeError: 'coroutine' object has no attribute 'first'`/`'all'`.
This affects every `get_review`/`list_reviews` test (13 of them); the `create_review` tests pass because they never touch `db.execute`/`result`.
Fix is test-only: build `mock_result` with `MagicMock()` instead of `AsyncMock()`, keeping `db.execute` itself as an `AsyncMock`.
No changes needed in `core/services/review_service.py`.


**Branch name:** fix/158-failing-async-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jgarcdev/PathReview/commit/8fd9aa7f0a09c9d355d2c4058834391266ef0138

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py -q`, which reproduced the exact numbers from the issue: 13 failed, 6 passed. All 13 failures trace back to `mock_result = AsyncMock()` in `get_review`/`list_reviews` tests, where `result.scalars()` resolves to an unawaited coroutine instead of a `MagicMock`, causing `.first()`/`.all()` to raise `AttributeError`.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** null

**Blockers or open questions:** null

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the PLAN.md fix in `tests/unit/test_review_service.py`: all 13 mis-mocked tests now build the `Result` mock with `MagicMock()` (renamed to `mockResult`) instead of `AsyncMock()`, while `mock_db_session.execute` stays an `AsyncMock` returning it. Also updated the `test_list_reviews_orders_by_created_at_desc` assertion from `assert_called_once()` to `call_count == 2` to match the count + paginated query calls. `pytest tests/unit/test_review_service.py -q` now shows 19 passed, 0 failed (up from 13 failed / 6 passed).

**Next steps:**
Commit the test changes, push the branch, and open the PR against `ascherj/pathreview` referencing issue #158.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/408

**Branch:** `fix/158-failing-async-tests`

**What you built:**
Fixed the async mock setup in `tests/unit/test_review_service.py` so the mocked SQLAlchemy `Result` object is a `MagicMock` (sync `.scalars()`/`.first()`/`.all()`) while `db.execute` remains an `AsyncMock`, matching the real async API. No changes were needed in `core/services/review_service.py`.

**Tests added or updated:**
Only `tests/unit/test_review_service.py`. Updated the mock construction in all 13 previously-failing `get_review`/`list_reviews` tests, and adjusted one assertion (`call_count == 2`) to reflect the count and paginated query calls.

**Self-review confirmation:** [x] make test-unit passes (for `test_review_service.py`: 19/19) [x] make check passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Nothing was particularly surprising.

**What did you learn about working in a large codebase?**
I learned that it can be overwhelming stepping inside someone else's code, especially with a relatively large base.

**How did AI tools help — and where did they fall short?**
AI assistance was useful in knowing the layout and flow of the logic and code.
However, I had to go through it myself to ensure.

**What would you do differently if you started over?**
None.

**What are you most proud of from this module?**
I am proud of making my first pull request.