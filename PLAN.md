## Solution plan

**Issue:** [#154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand
The problem is in `api/routes/health.py`. The `health_check()` function sends `"SELECT 1"` directly to `db.execute()`. In SQLAlchemy 2.x, a SQL string needs to be wrapped with `text()`. Because it is not wrapped, SQLAlchemy raises an error even when PostgreSQL is running.

The current result is that the PostgreSQL dependency is shown as unhealthy. In my local test, `GET /health` returns 503 because both PostgreSQL and Redis are unhealthy. After fixing Issue #154, PostgreSQL should be shown as healthy when the database is working, although the separate Redis problem in Issue #155 may still cause the endpoint to return 503.

### Map
- `api/routes/health.py` — existing file
  - Update the PostgreSQL probe in `health_check()` to call `db.execute(text("SELECT 1"))`.

- `tests/unit/test_health.py` — new file to create
  - Add one focused unit test confirming that the PostgreSQL probe passes a SQLAlchemy textual SQL object to `db.execute()`.

### Plan
1. Update the PostgreSQL probe in `api/routes/health.py` by importing `text` from SQLAlchemy and changing `db.execute("SELECT 1")` to `db.execute(text("SELECT 1"))`.
2. Add one focused regression test in `tests/unit/test_health.py` for the PostgreSQL probe.
3. Run the new test and the existing test suite to check that the change does not break other behavior.
4. Run the application and call `GET /health` again to confirm that PostgreSQL is reported as healthy.

### Inputs & outputs
- Current output: PostgreSQL is shown as `"unhealthy"` because the check fails when running the plain string `"SELECT 1"`.
- Expected output after the fix: PostgreSQL is shown as `"healthy"` because `text("SELECT 1")` runs successfully.

### Risks & unknowns
- The `/health` route also checks other services, so I am not sure yet how to test only the PostgreSQL part.
- I cannot confirm the fix only by checking the final HTTP status. I also need to check the PostgreSQL result in the response.

### Edge cases
- If PostgreSQL is working, it should show `"healthy"`.
- If PostgreSQL is not working, it should show `"unhealthy"`.
- If PostgreSQL is healthy but Redis is not, PostgreSQL should still show `"healthy"` even if `/health` returns 503.