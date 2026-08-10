## Solution plan

**Issue:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail
https://github.com/ascherj/pathreview/issues/158

### Understand

The issue is caused by incorrect mock configuration in the review service unit tests.

The production service correctly awaits `db.execute()`. After the awaited call returns, the service uses the SQLAlchemy result synchronously through calls such as `result.scalars().first()` and `result.scalars().all()`.

The tests currently create the returned result object using `AsyncMock`. This causes `scalars()` to behave asynchronously and return a coroutine instead of a normal scalar result.

Expected behavior:
- `db.execute()` is asynchronous and should be awaited.
- The result returned by `db.execute()` should support synchronous calls to `scalars()`, `first()`, and `all()`.

Actual behavior:
- The result object is mocked as asynchronous.
- `scalars()` produces a coroutine.
- Calling `.first()` or `.all()` on that coroutine raises `AttributeError`.

### Map

Files involved:

- `tests/unit/test_review_service.py`
  - Contains the incorrect result mocks.
  - This is the main file expected to change.

- `core/services/review_service.py`
  - Contains `create_review()`, `get_review()`, and `list_reviews()`.
  - Used to understand the expected database behavior.
  - No production code changes are currently expected.

### Plan

1. Identify every test in `tests/unit/test_review_service.py` where the result returned from `db.execute()` is created using `AsyncMock`.

2. Keep `mock_db_session.execute` asynchronous because the production code uses `await db.execute()`.

3. Replace the mocked SQLAlchemy result objects with synchronous `Mock` or `MagicMock` objects so `scalars()`, `first()`, and `all()` return normal mocked values.

4. Update the `list_reviews()` tests to correctly represent its two `db.execute()` calls: one for determining the total count and another for retrieving the paginated reviews.

5. Run `pytest tests/unit/test_review_service.py -q` and verify the review service tests pass without changing the production behavior.

### Inputs & outputs

Input:
A mocked asynchronous database session passed to `get_review()` and `list_reviews()`.

Expected output:
`db.execute()` remains awaitable, while the returned result behaves like a normal SQLAlchemy result object.

Calls such as:

- `result.scalars().first()`
- `result.scalars().all()`

should return configured mock values instead of coroutine objects.

### Risks & unknowns

- `list_reviews()` calls `db.execute()` twice, so some tests may need separate mock results for the count query and paginated query.
- Fixing the current coroutine errors may reveal additional assertions that are currently hidden by the earlier exception.
- Some tests may make assumptions about the number of times `db.execute()` is called.
- I need to verify whether `Mock` or `MagicMock` is the most appropriate representation of the SQLAlchemy result object.
- Production code should not be changed unless investigation shows an actual production bug.

### Edge cases

- `get_review()` returns an existing review.
- `get_review()` returns `None`.
- `list_reviews()` returns no reviews.
- `list_reviews()` returns multiple reviews.
- The count query and paginated query return different results.
- Custom page numbers and page sizes still work.
