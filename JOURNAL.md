# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`tests/unit/test_review_service.py` builds its mock `AsyncSession` so that `result.scalars()` returns a coroutine instead of a `MagicMock` result object. The service code in `review_service.py` correctly awaits `db.execute(...)`, but then calls the synchronous `.scalars().first()` / `.scalars().all()` on the returned object — since that object is itself an un-awaited coroutine, those calls raise `AttributeError: 'coroutine' object has no attribute 'first'` (and `'all'`). Running `pytest tests/unit/test_review_service.py -q` locally reproduces this exactly: 13 failed, 6 passed. The fix is entirely in the test file's mock setup — mock `db.execute` as an `AsyncMock` that resolves to a plain `MagicMock` result object (with `.scalars().first()`/`.scalars().all()` wired synchronously), rather than mocking `scalars()` itself as async. A successful fix makes all 19 tests in that file pass without touching the (already-correct) service code.

**Branch name:** fix/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
