## Solution plan

**Issue:** [Issue #154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand

The PostgreSQL health check in `api/routes/health.py` passes the raw string `"SELECT 1"` directly to SQLAlchemy’s `execute()` method.

The expected behavior is for the health check to execute the query successfully and report PostgreSQL as healthy when the database connection works.

The actual behavior under SQLAlchemy 2.x is that the raw string is rejected because textual SQL must be explicitly wrapped with SQLAlchemy’s `text()` function.

### Map

The primary file involved is:

- `api/routes/health.py`
  - `health_check()` function
  - PostgreSQL database probe
  - SQLAlchemy import section

I do not expect other application files or modules to require changes.

### Plan

1. Inspect `api/routes/health.py` and confirm the exact database health-check query.
2. Import `text` from SQLAlchemy.
3. Replace `await db.execute("SELECT 1")` with `await db.execute(text("SELECT 1"))`.
4. Review the resulting diff to ensure no unrelated health-check logic changed.
5. Run available formatting, linting, type-checking, or health-check tests and document any environment limitations.

### Inputs & outputs

**Input:**

- An active SQLAlchemy database session supplied through `Depends(get_db)`.
- The textual SQL query `SELECT 1`.

**Expected output:**

- SQLAlchemy treats the query as an explicit SQL statement.
- A working PostgreSQL connection is reported as `"healthy"`.
- A failed database connection continues to be caught by the existing exception-handling logic.

### Risks & unknowns

- `api/routes/health.py` contains existing Ruff and MyPy errors that may cause repository checks to fail even if this fix is correct.
- My local Docker environment may prevent me from running the complete application and integration tests.
- Changing code beyond the SQL statement could unintentionally alter the behavior of the Redis, external-service, or overall health checks.
- I need to confirm whether the repository expects a new automated test for this small compatibility change.

### Edge cases

- PostgreSQL is unavailable or the database session raises an exception.
- The query executes successfully but another dependency, such as Redis, is unhealthy.
- SQLAlchemy 2.x rejects an unwrapped raw SQL string.
- The health endpoint must preserve its current error response when required dependencies are unhealthy.
- The change should not modify the behavior of the Redis or external-service checks.