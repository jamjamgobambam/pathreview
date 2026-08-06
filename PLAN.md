## Solution plan

**Issue:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail (https://github.com/ascherj/pathreview/issues/158)

### Understand

In `app/services/review_service.py`, database operations use asynchronous execution with `await db.execute(...)`. The service code expects `db.execute()` to return a result object whose `.scalars()` method is synchronous, returning a scalar result chain that supports methods like `.first()` and `.all()`.

Currently, in `tests/unit/test_review_service.py`, the test fixtures mock `db.execute` such that calling `.scalars()` returns an unawaited coroutine rather than a synchronous result mock. This causes 13 of 19 unit tests to crash with `AttributeError: 'coroutine' object has no attribute 'first'` (or `'all'`). The goal is to restructure the mock database session fixture so `execute` is an `AsyncMock` returning a synchronous `MagicMock` result object, allowing the existing CRUD tests to execute and pass without altering production code.

### Map

- `tests/unit/test_review_service.py`: Main file requiring changes. Contains the database session fixtures and mock setups that need refactoring.
- `app/services/review_service.py`: Reference file to inspect exact query execution patterns (e.g., calls to `db.execute()`, `.scalars()`, `.first()`, and `.all()`) to ensure mock alignment.

### Plan

1. **Audit Fixtures:** Trace the `mock_db_session` (or equivalent database mock fixture) in `tests/unit/test_review_service.py` to identify how `db.execute` and its return values are configured.
2. **Refactor `db.execute` Mock Setup:** Update `db.execute` to be an `AsyncMock` whose return value is a synchronous `MagicMock` representing the SQLAlchemy `Result` object.
3. **Configure Sync Scalar Chaining:** Set up `result_mock.scalars.return_value` as a `MagicMock` so that synchronous chained calls like `.scalars().all()` and `.scalars().first()` return the expected test model instances or lists.
4. **Verify Test Suite:** Run `pytest tests/unit/test_review_service.py -q` to confirm all 19 unit tests pass without errors.

### Inputs & outputs

- **Inputs:** Async mock database session objects injected into `review_service` function calls during unit tests.
- **Outputs:** `await db.execute(...)` resolves asynchronously to a mock result; synchronous calls to `.scalars().first()` or `.scalars().all()` on that result return mock entities or `None` as expected by `review_service.py`.

### Risks & unknowns

- **Shared Fixture State (`tests/unit/test_review_service.py`):** Modifying a shared session fixture might cause side effects across tests that expect different return shapes (e.g., scalar list vs. single object vs. `None`). Each test must be able to override return values cleanly.
- **Multiple Query Execution Paths (`app/services/review_service.py`):** Service functions that perform multiple database calls per routine may overwrite or re-use the same mock result unless `side_effect` or distinct return values are set for sequential `db.execute` calls.

### Edge cases

1. **Empty Result Queries:** Tests asserting that a review or entity does not exist must have `.scalars().first()` return `None` (or `.scalars().all()` return `[]`) cleanly without raising `StopIteration` or returning a truthy mock.
2. **Sequential Query Chains:** Service methods executing multiple distinct SQL queries within a single function call must handle `db.execute.side_effect = [mock_result_1, mock_result_2]` so that mock responses match each query in sequence.
