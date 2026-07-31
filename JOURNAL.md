# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Selection reasoning:**
I chose a Tier 1 issue because this is my first time contributing to a large, multi-layered public codebase. Before picking an issue, I considered the scope: Tier 1 issues are self-contained and don't require deep knowledge of the full system, which makes them a good fit for getting oriented. Issue #158 is a test-only fix — it doesn't touch production logic, has a clearly described failure mode with exact reproduction steps, and the fix is well-scoped to a single file. That made it a realistic starting point while I'm still learning how the project is structured.

**Problem summary:**
The `review_service` unit tests incorrectly configure their mock database session: `result.scalars()` is set up to return a coroutine, but the actual service code awaits `db.execute(...)` and then calls `.scalars().first()` / `.scalars().all()` on the synchronous result object. This mismatch causes `AttributeError: 'coroutine' object has no attribute 'first'` (and `'all'`) in 13 of the 19 tests, even though the service logic itself is correct. The fix is to rework the mock setup so `db.execute` is an `AsyncMock` and the returned result object uses `MagicMock` for `scalars()`, allowing the attribute chain to resolve properly and letting the existing CRUD tests actually run and pass.

**Branch name:** fix/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/melmel812/pathreview/commit/3953e33

**Reproduction summary:**
Running `pytest tests/unit/test_review_service.py -q` produces 13 failures with `AttributeError: 'coroutine' object has no attribute 'first'` (and `'all'`) inside `core/services/review_service.py`. The failures are caused by tests setting `mock_result = AsyncMock()`, which makes `.scalars` an `AsyncMock` — calling it returns a coroutine instead of a plain Mock, so the service's `.scalars().first()` and `.scalars().all()` calls fail.

**PLAN.md link:** https://github.com/melmel812/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
`list_reviews` calls `db.execute` twice (count query + page query). After fixing `mock_result` to `MagicMock`, both calls return the same mock — need to verify test assertions are loose enough, or use `side_effect` to return separate mocks per call.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all sub-tasks from PLAN.md. Replaced `AsyncMock()` with `MagicMock()` for all 13 `mock_result` instances in `tests/unit/test_review_service.py`. Also fixed a secondary broken assertion in `test_list_reviews_ordered_by_created_at` which used `assert_called_once()` but `list_reviews` calls `db.execute` twice (count query + page query). Added `MagicMock` to the imports.

**Next steps:**
Run `make check` and `make test-unit`, confirm no new failures introduced, open the PR.

**Blockers:**
None — `make check` has pre-existing failures across the codebase unrelated to this fix; my changes introduce no new errors.

---

### Check-in 2 (end of week)

**PR link:** [to be filled]

**Branch:** `fix/158-review-service-async-mocks`

**What you built:**
Replaced `AsyncMock()` with `MagicMock()` for all 13 mock result objects in `tests/unit/test_review_service.py`. Because `AsyncMock` makes child attribute calls return coroutines, the service's synchronous `.scalars().first()` and `.scalars().all()` calls were raising `AttributeError`. Switching to `MagicMock` makes those calls return plain `Mock` objects as expected. Also fixed one incorrect `assert_called_once()` assertion that failed to account for `list_reviews` making two `db.execute` calls.

**Tests added or updated:**
Modified `tests/unit/test_review_service.py` — all 13 previously failing tests now pass by correcting the `AsyncMock` → `MagicMock` mock setup on the result object. One additional assertion (`test_list_reviews_ordered_by_created_at`) updated from `assert_called_once()` to `assert call_count == 2` to match the actual service behavior. All 19 tests now pass.

**Self-review confirmation:** [x] make check passes (pre-existing failures only, no new failures introduced)  [x] make test-unit passes

**Draft PR feedback received from:** none
