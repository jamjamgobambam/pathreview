## Solution plan

**Issue:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail [#158](https://github.com/ascherj/pathreview/issues/158)

### Understand

The test suite incorrectly uses `AsyncMock` for the return values of synchronous database query results. Because of this, chained methods like `.scalars().first()` evaluate as coroutines instead of returning the expected mocked objects, causing `AttributeError`s inside the otherwise correct service code.

### Map

The only file that needs to be touched is:

- `tests/unit/test_review_service.py`

### Plan

1. Import `MagicMock` from `unittest.mock` at the top of the test file.
2. Locate all 13 instances of `mock_result = AsyncMock()` that are used to mock `db.execute()` returns.
3. Change those specific `AsyncMock` assignments to `MagicMock()`.
4. Update the faulty assertion in `test_list_reviews_ordered_by_created_at` from `assert_called_once()` to `assert mock_db_session.execute.call_count == 2`, because the `list_reviews` function actually executes two separate queries (one for the total count, one for the data).

### Inputs & outputs

The fix takes the existing test environment and injects synchronous `MagicMock` objects as the output of the database query mocks, simulating how SQLAlchemy synchronously handles result chains.

### Risks & unknowns

One risk is accidentally changing a genuine asynchronous call to a synchronous mock. We must be careful to leave `mock_db_session.execute = AsyncMock(...)` alone, because the `.execute()` method itself is `async` and must remain an `AsyncMock`.

### Edge cases

We must ensure that the fix handles the pagination logic gracefully—specifically, recognizing that fetching paginated lists inherently requires two queries, which breaks any pre-existing tests that strictly asserted only a single database call was made.
