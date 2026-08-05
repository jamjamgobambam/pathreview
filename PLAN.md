## Solution plan

**Issue:** #154 - Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x  
https://github.com/ascherj/pathreview/issues/154

### Understand
The PostgreSQL probe in `api/routes/health.py` calls `await db.execute("SELECT 1")`, which passes textual SQL to SQLAlchemy as a plain Python string. The project uses SQLAlchemy 2.x, which requires textual SQL to be explicitly wrapped with `sqlalchemy.text()` before it is passed to `AsyncSession.execute()`.

I reproduced the issue locally using SQLAlchemy 2.0.51 and the project's real `AsyncSession`. The raw `"SELECT 1"` string raised `sqlalchemy.exc.ArgumentError`, while `text("SELECT 1")` succeeded through the same database session and returned `1`. Docker also reported the PostgreSQL service as healthy, confirming that the failure was caused by the query format rather than an unavailable database.

Inside `health_check()`, the exception is caught by the PostgreSQL probe's exception handler. The route then marks PostgreSQL and the overall health status as `"unhealthy"`. This causes the route to raise an HTTPException, which FastAPI returns as an HTTP 503 response even though PostgreSQL is reachable.

The expected behavior is that a reachable PostgreSQL database is reported as `"healthy"`. The route should continue to report PostgreSQL as `"unhealthy"` when the database execute operation fails because the database is genuinely unavailable.

**Root cause:** The PostgreSQL health probe does not wrap the textual SQL statement with SQLAlchemy's `text()` construct before passing it to `AsyncSession.execute()`.

### Map

- `api/routes/health.py`
  - Relevant function: `health_check()`
  - This file contains the PostgreSQL probe that currently calls `await db.execute("SELECT 1")`.
  - I expect to import SQLAlchemy's `text()` function and wrap the query before passing it to `db.execute()`.

- `tests/unit/test_health.py`
  - This file does not currently exist, so I expect to create it.
  - It will contain regression tests for the PostgreSQL portion of `health_check()`.
  - The tests will follow the project's existing async unit-test conventions using `pytest.mark.unit`, `pytest.mark.asyncio`, and `AsyncMock`.

### Plan

1. Update `api/routes/health.py` to import SQLAlchemy's `text()` function and replace `await db.execute("SELECT 1")` with `await db.execute(text("SELECT 1"))`. Keep the existing logging, dependency status updates, and HTTP 503 behavior unchanged.

2. Create `tests/unit/test_health.py` using the repository's existing async test conventions: `pytest.mark.unit`, `pytest.mark.asyncio`, and `AsyncMock`. Mock the Redis check so that unrelated Redis configuration behavior does not affect the PostgreSQL tests.

3. Add a regression test for the successful database path. The test should call `health_check()` with a mock database session whose `execute()` method succeeds, then verify that `execute()` receives a SQLAlchemy textual SQL object and that PostgreSQL is reported as `"healthy"`.

4. Add a test for the database failure path. Configure the mock session's `execute()` method to raise an exception, then verify that the route still marks PostgreSQL as `"unhealthy"` and raises an HTTP 503 response with the existing health-status structure.

5. Run the new health tests directly, then run `make check`. Run `make test-unit` afterward and compare the results with the existing baseline of 53 failures and 375 passing tests to confirm that the change introduces no additional failures.

### Inputs & outputs

**Function involved:** `health_check(db)`

**Current input to the PostgreSQL probe:**
- A database session provided by FastAPI through `get_db()`.
- The plain Python string `"SELECT 1"` passed to `db.execute()`.

**Current output:**
- SQLAlchemy 2.x raises `sqlalchemy.exc.ArgumentError` before the query reaches PostgreSQL.
- `health_check()` catches the exception and marks PostgreSQL and the overall health status as `"unhealthy"`.
- The route raises an HTTP 503 response even when PostgreSQL is running and reachable.

**Expected input after the fix:**
- The same database session.
- A SQLAlchemy textual SQL object created with `text("SELECT 1")`.

**Expected output after the fix:**
- When PostgreSQL is reachable, `db.execute(text("SELECT 1"))` completes successfully and PostgreSQL is marked as `"healthy"`.
- The existing health-response structure, logging, and handling of the other dependencies remain unchanged.
- When the database execution genuinely fails, PostgreSQL is still marked as `"unhealthy"` and the route still raises HTTP 503.

**Regression tests:**
- A successful database probe should verify that `db.execute()` receives a SQLAlchemy `TextClause` containing `"SELECT 1"` rather than a plain string.
- A failed database probe should verify that an exception from `db.execute()` still produces the existing unhealthy PostgreSQL status and HTTP 503 behavior.

### Risks & unknowns

1. **The PostgreSQL test could be affected by unrelated dependency checks.**  
   `health_check()` continues to check Redis and the vector database after the PostgreSQL probe. The route currently refers to `settings.redis_host` and `settings.redis_port`, but `core/config.py` only defines `redis_url`. The health tests will need to isolate or mock the Redis check so that this separate configuration issue does not cause a false failure or expand the scope of issue #154.

2. **The success test could become too dependent on SQLAlchemy internals.**  
   A newly created `text("SELECT 1")` object may not compare directly with another `text("SELECT 1")` object. Instead of relying on object identity, the test should inspect the argument passed to `db.execute()`, confirm that it is a SQLAlchemy textual SQL object, and confirm that its SQL content is `"SELECT 1"`.

3. **The failure-path test must preserve the existing response behavior.**  
   When `db.execute()` raises, `health_check()` should still mark PostgreSQL and the overall status as `"unhealthy"` and raise `HTTPException` with status code 503. The test setup must prevent unrelated Redis or vector database behavior from changing the response being asserted.

4. **The repository already has unrelated unit-test failures.**  
   The baseline `make test-unit` run produced 53 failures and 375 passing tests in modules unrelated to the health route. I should not attempt to fix those failures as part of issue #154. I will validate the new health tests directly, run `make check`, and compare the full unit-test result with the baseline to confirm that my change does not add new failures.

### Edge cases

- **PostgreSQL is reachable:** The wrapped `text("SELECT 1")` query should execute successfully, and the PostgreSQL dependency should be reported as `"healthy"`.

- **PostgreSQL is unavailable or the query execution raises:** The existing exception handler should still mark PostgreSQL and the overall health status as `"unhealthy"` and raise an HTTP 503 response.

- **PostgreSQL is healthy but Redis is unavailable:** The PostgreSQL result should remain `"healthy"`, while the route may still return an unhealthy overall status because another dependency failed. The fix should not change how dependency results are recorded separately.

- **The vector database URL is missing:** The existing behavior should remain unchanged, with the vector database reported as `"unavailable"` without altering the PostgreSQL result.

- **The database execute call succeeds but returns no meaningful row data:** The health probe only needs successful query execution. It should not depend on processing or storing the returned result.

- **The health response structure must remain stable:** The fix should not remove or rename the existing `status`, `dependencies`, `safety_events_last_hour`, or `timestamp` fields.