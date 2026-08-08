## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand

The PostgreSQL health check in `api/routes/health.py` passes the raw string `"SELECT 1"` to `db.execute()`. SQLAlchemy 2.x requires textual SQL statements to be explicitly wrapped with `sqlalchemy.text()`. The current behavior raises an `ArgumentError`, marks PostgreSQL as unhealthy, and contributes to a 503 response even when the database is available. The expected behavior is for the database probe to execute successfully and mark PostgreSQL as healthy when the connection works.

### Map

Files expected to be involved:

- `api/routes/health.py` — import `text` and update the PostgreSQL database probe.
- `tests/unit/test_health.py` — add or update tests for the health-check database behavior. If this test file does not exist, it will be created following the repository’s existing unit-test structure.

The affected function is:

- `health_check()` in `api/routes/health.py`

### Plan

1. Import SQLAlchemy’s `text` function in `api/routes/health.py`.
2. Replace `await db.execute("SELECT 1")` with an explicitly declared textual SQL statement.
3. Add a unit test that verifies the database session receives the correctly wrapped statement and PostgreSQL is reported as healthy when execution succeeds.
4. Add a failure-path test confirming that a genuine database exception still marks PostgreSQL as unhealthy.
5. Run the focused health-check tests and the relevant unit-test suite to confirm the fix does not change unrelated health-check behavior.

### Inputs & outputs

The database probe takes an asynchronous SQLAlchemy database session supplied through FastAPI’s `get_db` dependency. When the database is reachable, the corrected probe should execute `SELECT 1` without an SQLAlchemy `ArgumentError` and set `dependencies.postgres` to `"healthy"`. When database execution genuinely fails, it should continue to set PostgreSQL and the overall health status to `"unhealthy"`.

### Risks & unknowns

The health endpoint also checks Redis and the vector database, so another unhealthy dependency may still cause the complete endpoint to return 503 after the PostgreSQL fix. Tests should isolate the PostgreSQL behavior so unrelated dependency checks do not hide the result. I also need to confirm whether a health-route test file already exists before creating `tests/unit/test_health.py` and follow the mocking patterns used elsewhere in the test suite.

### Edge cases

- The database is reachable and `SELECT 1` succeeds.
- The database session raises a connection-related exception.
- PostgreSQL is healthy while Redis or the vector database is unavailable.
- A mocked asynchronous database session is used in unit tests.
- The health endpoint must preserve its existing response structure and status-handling behavior.