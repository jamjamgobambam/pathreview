## Solution plan

**Issue:** review_service unit tests misconfigure async mocks - 13 of 19 tests fail (https://github.com/ascherj/pathreview/issues/158)

### Understand
I reproduced the issue locally by running `pytest tests/unit/test_review_service.py -q` in the project venv. The current result is **13 failed, 6 passed**, and failing tests consistently crash with `AttributeError: 'coroutine' object has no attribute 'first'` or `'all'`.

The service code in `core/services/review_service.py` awaits `db.execute(...)`, then uses sync-style SQLAlchemy result methods (`result.scalars().first()` and `result.scalars().all()`). The failing tests in `tests/unit/test_review_service.py` currently mock this result chain with `AsyncMock` in places where sync-style result objects are expected, so `scalars()` returns a coroutine and downstream calls fail.

**Root cause:** async/sync boundary is mocked incorrectly in tests, not in service logic.

### Map
Files and modules involved:
- `tests/unit/test_review_service.py` (failing tests and repeated mock setup)
- `core/services/review_service.py` (source of the execute/scalars contract)
- `tests/conftest.py` (optional, if shared helper fixture is needed)

Primary functions/paths expected to be affected:
- `get_review()` and `list_reviews()` test paths (where first/all are called)
- Any helper fixture that constructs mocked execute return values

### Plan
1. Keep a reproduction record in `JOURNAL.md` with exact command and observed failures to prove the issue is real on this branch.
2. Refactor failing tests in `tests/unit/test_review_service.py` so `db.execute` stays `AsyncMock`, but `execute.return_value` is a sync result-like object for `scalars().first()` and `scalars().all()`.
3. Add a tiny helper fixture/factory (in test file or `tests/conftest.py`) to avoid repeated ad hoc result-chain mocks across CRUD tests.
4. Re-run `pytest tests/unit/test_review_service.py -q` to confirm issue-specific failures are resolved.
5. Run adjacent review-related unit tests to verify no regressions from fixture changes.

### Inputs & outputs
Inputs:
- AsyncSession-like mock object used by review service tests
- Query-path mock payloads for single-row (`first`) and multi-row (`all`) behavior
- Existing review fixture objects and UUID test inputs

Outputs:
- Correct async/sync boundary in mock setup (await `execute`, sync `scalars` chain)
- `tests/unit/test_review_service.py` passing where it currently fails
- More maintainable/reusable test mock wiring

### Risks & unknowns
1. If a shared fixture is changed in `tests/conftest.py`, other modules may fail due to altered mock defaults.
2. After fixing mock wiring, some tests may still fail for real behavior mismatches in assertions.
3. Over-constraining with `spec`/`autospec` on SQLAlchemy-like result objects could make tests brittle.

### Edge cases
1. No rows returned: `scalars().first()` returns `None` and tests assert expected behavior.
2. Multiple rows returned: `scalars().all()` returns list and total count is computed correctly.
3. Execute exceptions: tests should still verify error propagation paths.
4. Multiple service calls in one test: mock state must not leak between query calls.
