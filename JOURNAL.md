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

**Reproduction commit link:** null

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py -q`, which reproduced the exact numbers from the issue: 13 failed, 6 passed. All 13 failures trace back to `mock_result = AsyncMock()` in `get_review`/`list_reviews` tests, where `result.scalars()` resolves to an unawaited coroutine instead of a `MagicMock`, causing `.first()`/`.all()` to raise `AttributeError`.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** null

**Blockers or open questions:** null