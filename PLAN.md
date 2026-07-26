## Solution plan

**Issue:** [review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

### Understand
`tests/unit/test_review_service.py` builds `mock_result = AsyncMock()` to stand in for the object returned by `await db.execute(...)`. In real SQLAlchemy, `execute()` is the only genuinely async step — the `Result` object it resolves to (`.scalars()`, `.first()`, `.all()`) is used synchronously afterward. Because `mock_result` has no `spec`, its child attributes (`.scalars`, `.first`, `.all`) auto-inherit `AsyncMock`, so calling them returns a live coroutine instead of the configured `return_value`. The real `review_service.py` code calls `.scalars().first()`/`.scalars().all()` without `await` (matching real SQLAlchemy), so it ends up doing `coroutine.first()` / `coroutine.all()`, which raises `AttributeError: 'coroutine' object has no attribute 'first'/'all'`.

Expected: all 19 tests in the file pass.
Actual: 13 of 19 fail with the `AttributeError` above; only the 6 `create_review` tests pass, since they never touch `mock_result`.

### Map
`tests/unit/test_review_service.py`
- Import line (currently `from unittest.mock import AsyncMock, Mock, patch`) needs `MagicMock` added.
- 13 occurrences of `mock_result = AsyncMock()` across the `get_review` and `list_reviews` test methods.

No production code (`core/services/review_service.py`) needs to change — the bug is entirely in the test file's mock setup.

### Plan
1. Add `MagicMock` to the `unittest.mock` import.
2. Replace all 13 `mock_result = AsyncMock()` occurrences with `mock_result = MagicMock()`.
3. Leave `mock_db_session.execute = AsyncMock(return_value=mock_result)` as-is — `execute()` genuinely is async, so this part is already correct.
4. Run `pytest tests/unit/test_review_service.py -v` and confirm all 19 tests pass.
5. Spot-check the diff to make sure no `AsyncMock()` was swapped in the 6 already-passing `create_review` tests (they don't use `mock_result`, so should be unaffected).

### Inputs & outputs
Input: the current (broken) `tests/unit/test_review_service.py`.
Output: the same file with `mock_result` built as `MagicMock()` instead of `AsyncMock()`, no other logic changed, full test suite green.

### Risks & unknowns
- Need to double check none of the 13 call sites rely on any part of `mock_result` actually being awaited elsewhere in the same test (a quick grep/read confirms they don't — `mock_result` is only ever accessed via `.scalars().first()`/`.scalars().all()`, both synchronous in real SQLAlchemy).
- `mock_db_session` itself (from the `mock_db_session` fixture) stays `AsyncMock()` — that's correct and shouldn't be touched, since `commit`/`refresh`/`execute` are all genuinely async in real `AsyncSession`.

### Edge cases
Not really applicable — this is a test-infrastructure fix, not new behavior. The only thing to verify post-fix is that the previously-passing `create_review` tests (which don't touch `mock_result`) still pass unchanged.
