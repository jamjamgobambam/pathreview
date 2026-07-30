# Solution plan

**Issue:** [review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

### Understand
Only `db.execute(stmt)` is async in SQLAlchemy's async API where the `Result` it returns
is sync (`.scalars()`, `.first()`, `.all()` are plain methods). Tests build
`mock_result = AsyncMock()`, so `result.scalars()` returns an unawaited coroutine
instead of the configured mock, and `.first()`/`.all()` on it raises `AttributeError`.
Confirmed via `pytest tests/unit/test_review_service.py -q` -> 13 failed, 6 passed
(matches issue). Failures are all `get_review`/`list_reviews` tests; passing tests
(`create_review`) never touch `db.execute`.

### Map
- `tests/unit/test_review_service.py`: 13 tests build `mock_result = AsyncMock()`;
  change to `MagicMock()` (fixture-level fix, no other files affected).
- `core/services/review_service.py`: `get_review`/`list_reviews`; read-only reference,
  no changes needed (already awaits/calls correctly).

### Plan
1. In each of the 13 failing tests, change `mock_result = AsyncMock()` to
   `mock_result = MagicMock()` so `.scalars()` returns a plain Mock rather than a
   coroutine.
2. Keep `mock_db_session.execute = AsyncMock(return_value=mock_result)` unchanged, `db.execute(...)` must still be awaitable.
3. Re-run `pytest tests/unit/test_review_service.py -q` and confirm all 19 tests pass
   with no `RuntimeWarning: coroutine ... was never awaited` warnings.
4. Optionally, replace the ad-hoc `AsyncMock()`/`MagicMock()` result construction with
   a small shared fixture/helper (e.g. `make_execute_result(scalars_first=None,
   scalars_all=None)`) to avoid repeating the pattern 13 times and to prevent the same
   mistake from recurring in future tests.
5. Double check `test_create_review_*` tests still pass unmodified (they don't touch
   `db.execute`, so they're out of scope for this fix).

### Inputs & outputs
Input: the existing test file with 13 mis-mocked `Result` objects.
Output: same test file, same assertions, only the mock construction changed
(`AsyncMock()` -> `MagicMock()` for `mock_result`). No changes to
`core/services/review_service.py`, since its async/await usage is already correct.

### Risks & unknowns
- Must not accidentally make `mock_db_session.execute` itself synchronous, only the
  `Result` object it returns should become a `MagicMock`.
- If a future test needs to await something on `result`, this fix would need revisiting.
- Should verify no other test files in the repo share this same anti-pattern (e.g.
  other service tests mocking `db.execute` results as `AsyncMock`).

### Edge cases
- `test_get_review_returns_none_for_wrong_user`: `.first()` returns `None`, it must still
  work with `MagicMock`.
- Empty list results (`test_list_reviews_page_2_returns_correct_offset`,
  `test_list_reviews_custom_page_size`, etc.) where `.all()` returns `[]`, it must not be
  coerced into a coroutine either.