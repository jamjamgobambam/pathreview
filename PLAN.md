## Solution plan

**Issue:** [review_service unit tests misconfigure async mocks — 13 of 19 tests fail](https://github.com/ascherj/pathreview/issues/158)

### Understand

The production review service correctly awaits `db.execute()` because it uses an asynchronous database session. However, the returned SQLAlchemy result object exposes synchronous methods such as `scalars()`, `first()`, and `all()`. The tests incorrectly represent this result object with `AsyncMock`, causing those synchronous methods to return coroutine objects. The expected behavior is for the mocked result methods to immediately return review objects, lists, or scalar values, but the actual tests raise `AttributeError` before reaching their intended assertions.

### Map

The files involved are:

- `tests/unit/test_review_service.py` — contains the incorrectly configured database result mocks and will be modified.
- `core/services/review_service.py` — contains the production behavior exercised by the tests and will be inspected for reference, but should not require modification.
- `REPRODUCTION.md` — records the command, failure count, and observed errors that reproduce the issue.

### Plan

1. Identify every test in `tests/unit/test_review_service.py` that represents a SQLAlchemy result object with `AsyncMock`.
2. Keep the database session's `execute()` method asynchronous by configuring it with `AsyncMock`.
3. Replace returned result objects with synchronous `Mock` instances and configure chained calls such as `scalars().first()` and `scalars().all()` to return the expected test data.
4. Configure `side_effect` with separate result mocks for service methods that call `execute()` multiple times.
5. Run the targeted test file and the broader unit-test suite to confirm the review service tests pass without changing production behavior.

### Inputs & outputs

The inputs are mocked database sessions, review identifiers, profile identifiers, review data, and predefined model objects used by the existing unit tests. The fix should produce correctly configured synchronous result objects so the service receives the same values that a real SQLAlchemy result would return. The expected final output is all 19 tests in `tests/unit/test_review_service.py` passing.

### Risks & unknowns

A single service method may call `db.execute()` more than once, requiring result mocks to be supplied in the correct order through `side_effect`. Different queries may also use different result access patterns, so applying one identical mock configuration everywhere could hide errors or return the wrong data. Another risk is accidentally changing `db.execute()` itself to a synchronous mock, which would no longer match the real `AsyncSession` interface. The production service should only be changed if further investigation proves that it has an independent defect.

### Edge cases

The mock setup must correctly handle:

- Queries that return one review through `scalars().first()`.
- Queries that return multiple reviews through `scalars().all()`.
- Queries that return no matching review.
- Service methods that execute multiple queries.
- Count or scalar queries that return numeric values.
- Exceptions raised by the mocked database session.
