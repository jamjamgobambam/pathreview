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
