## Solution plan

**Issue:** #158 review_service unit tests misconfigure async mocks — 13 of 19 tests fail
https://github.com/ascherj/pathreview/issues/158

### Understand
The root cause is a structural misconfiguration of asynchronous database session mock objects within the service unit test suite. The core application logic in `core/services/review_service.py` correctly handles asynchronous operations by running `result = await db.execute(stmt)` and subsequently evaluating the results synchronously using chained methods like `result.scalars().first()` or `result.scalars().all()`. 

However, 13 of the unit tests mock this execution path by setting up `mock_result = AsyncMock()`. Because `AsyncMock` recursively returns new coroutine mock instances for any accessed properties or method invocations, calling `result.scalars()` unexpectedly evaluates to an asynchronous coroutine instead of a standard synchronous object. When the service layer attempts to execute `.first()` or `.all()` on this coroutine, Python raises an `AttributeError: 'coroutine' object has no attribute 'first'`. 

The expected behavior is for `db.execute` (an `AsyncMock`) to return a standard synchronous `Mock` or `MagicMock` representing the database `Result` set, allowing subsequent synchronous method chaining to execute cleanly.

### Map
Files I expect to touch:
* `tests/unit/test_review_service.py` — I will rewrite the internal configuration of the `mock_db_session` fixture and modify the individual setups inside the 13 failing test cases to return synchronous result mock objects.
* No production files (`core/services/review_service.py`) will be modified, as the underlying application code is entirely correct.

### Plan
1. **Isolate the Test Environment:** Run `pytest tests/unit/test_review_service.py -v` to confirm the exact baseline profile of 13 failures and 6 successes.
2. **Refactor the Database Response Mocks:** Update individual failing test blocks (such as `test_get_review_returns_review_for_correct_owner`) to configure `mock_result = Mock()` (or `MagicMock`) instead of `AsyncMock()`.
3. **Correct the Execution Return Values:** Alter the mock session assignment from `mock_db_session.execute = AsyncMock(return_value=mock_result)` to `mock_db_session.execute.return_value = mock_result` so that the already declared `AsyncMock` from the fixture passes back a synchronous mock container when awaited.
4. **Execute Verification Passes:** Run the test file locally using `pytest tests/unit/test_review_service.py` to confirm that all 19 tests pass successfully.
5. **Enforce Project Standards:** Run `make check` (or manually run `ruff check .`, `black .`, and `mypy`) to ensure that the modifications meet all style, format, and static typing validation standards.

### Inputs & outputs
* **Fixtures/Functions Changing:** `mock_db_session` fixture and test methods within `tests/unit/test_review_service.py`.
* **Input State:** An active `AsyncMock` session object executing an algebraic SQLAlchemy statement layer.
* **Output State:** A combined mock topology where `await mock_db_session.execute(stmt)` cleanly evaluates to a synchronous mock instance supporting standard `.scalars().all()` and `.scalars().first()` calls.

**Test Specification Code Block:**
```python
# Target configuration for verification inside test methods:
mock_result = Mock()  # Synchronous Mock representing the SQLAlchemy Result
mock_result.scalars.return_value.first.return_value = mock_review
mock_db_session.execute.return_value = mock_result  # Evaluates correctly when awaited
```

### Risks & unknowns

1. **Mypy Static Typing Inferences**: Because `mock_db_session` is an `AsyncMock`, aggressively changing underlying return values to mix sync and async layers might cause `mypy` typing checks to complain about implicit `Any` variables or strict type mismatches. I will verify type cleanliness using `make check`.

2. **Shared Fixture Interference**: Changing how `execute` handles default returns inside the core `mock_db_session` fixture could inadvertently break the 6 passing tests that depend on specific initialization properties. I will modify the case allocations on a per-test basis first to maintain isolation.

### Edge cases

* **Empty Database Queries**: Tests checking for missing records (`test_get_review_returns_none_for_wrong_user`) must have their synchronous `mock_result.scalars.return_value.first.return_value` securely assigned to `None` without falling back to a nested coroutine block.

* **Pagination & Counts**: Tests that evaluate result lengths via `len(count_result.scalars().all())` must return an actual iterable array/list layout (e.g., `[]` or a list of mock objects) to prevent `TypeError` validations on sizing calculations.