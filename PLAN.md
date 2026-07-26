# PLAN.md

## Solution plan

**Issue:** [review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

### Understand

**Root cause:** Every failing test builds its mock result object as `AsyncMock()`:
```python
mock_result = AsyncMock()
mock_result.scalars.return_value.first.return_value = mock_review
```
Because `mock_result` is an `AsyncMock`, its child attribute `mock_result.scalars` is also an `AsyncMock`. Calling an `AsyncMock` returns a *coroutine object* — not the `.return_value`. So when the service does `result.scalars().first()`, it calls `.first()` on a coroutine, which raises `AttributeError: 'coroutine' object has no attribute 'first'` (and `'all'` for list queries).

**Expected behavior:** `db.execute()` is awaited; the result is a plain SQLAlchemy result object. Calling `.scalars()` on it returns a synchronous scalar iterator, and `.first()` / `.all()` work without any awaiting.

**Actual behavior:** 13 of 19 tests raise `AttributeError` at the `.scalars().first()` / `.scalars().all()` call inside the service.

### Map

Files involved:
- `tests/unit/test_review_service.py` — the only file that needs to change; all 13 broken tests set `mock_result = AsyncMock()`
- `core/services/review_service.py` — service logic is correct; no changes needed here

### Plan

1. **Replace `AsyncMock()` with `MagicMock()`** for every `mock_result` variable in `test_review_service.py`. `MagicMock` makes `.scalars()` return a regular Mock, so `.first()` and `.all()` resolve correctly.
2. **Verify the fixture** — the shared `mock_db_session` fixture already sets `session.execute = AsyncMock()`, which is correct (execute itself is awaited). No change needed there.
3. **Run the test suite** after the fix and confirm all 19 tests pass.
4. **Check for the same pattern** in any other unit test files that mock SQLAlchemy sessions, and apply the same fix if found.
5. **Commit** with a clear message referencing issue #158.

### Inputs & outputs

- **Input:** The broken test file with `mock_result = AsyncMock()` in 13 tests.
- **Output:** The same tests using `mock_result = MagicMock()`, making `.scalars().first()` and `.scalars().all()` return configured values instead of raising `AttributeError`. All 19 tests should pass with no changes to production code.

### Risks & unknowns

- Some tests call `mock_db_session.execute` multiple times (e.g. `list_reviews` calls it twice — once for count, once for page). These tests currently use a single `mock_result` for both calls. After the fix, both calls return the same mock, which may cause the count and the page result to be identical. Need to verify the assertions in those tests are loose enough to pass, or configure `side_effect` to return different mocks per call.
- No risk to production code — this is a test-only change.

### Edge cases

- `list_reviews` calls `db.execute` twice (once for the count query, once for the paginated results query). After switching to `MagicMock`, both calls return the same mock object by default. If a test asserts that `total` equals the length of `reviews`, the shared mock means both calls return the same `.all()` list — the assertion would pass coincidentally. The fix must use `side_effect=[count_result, page_result]` on `execute` so each call returns an independent mock, making the count and page results independently controllable.
- `get_review` should return `None` when no matching review exists (e.g. wrong `user_id` or non-existent `review_id`). After the fix, `mock_result.scalars.return_value.first.return_value = None` must resolve to actual `None` — not a Mock object — so the caller can do `if result is None` checks. This needs to be verified after switching to `MagicMock` since `MagicMock()` attributes default to new `MagicMock` instances, not `None`.
