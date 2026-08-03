# Solution Plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Issue link:** https://github.com/ascherj/pathreview/issues/154

---

## Understand

The application's health check verifies that PostgreSQL is available by executing a simple `SELECT 1` query. The current implementation passes this query directly to SQLAlchemy as a plain Python string. SQLAlchemy 2.x requires textual SQL statements to be wrapped using the `text()` function. Because of this, the health check incorrectly reports PostgreSQL as unavailable even when the database is running normally. The expected behavior is for the health endpoint to accurately report the database status when PostgreSQL is healthy.

---

## Map

### Files involved

- `api/routes/health.py` — contains the PostgreSQL health check logic that executes the database query.
- Health check test files (if available) — verify that the health endpoint behaves correctly after the fix.
- `PLAN.md` and `JOURNAL.md` — document the investigation, reproduction, and implementation plan.

---

## Plan

1. Reproduce the issue by starting the application and calling the `/health` endpoint.
2. Locate the PostgreSQL health check implementation in `api/routes/health.py`.
3. Replace the raw SQL string with SQLAlchemy's `text()` function so the query is compatible with SQLAlchemy 2.x.
4. Verify that the health endpoint correctly reports PostgreSQL as healthy when the database is running.
5. Run existing tests (or add/update a health check test if necessary) to confirm the fix works correctly and prevent regressions.

---

## Inputs & Outputs

### Input

- GET `/health` request
- PostgreSQL database connection
- SQLAlchemy database session

### Output

- PostgreSQL health status is reported correctly.
- The health endpoint accurately reflects the database availability.
- Compatibility with SQLAlchemy 2.x is restored.

---

## Risks & Unknowns

- Confirm that replacing the raw SQL string with `text()` fully resolves the issue.
- Determine whether the project already includes tests for the health endpoint or whether a new test should be added.
- Verify that the change does not affect the Redis or Vector DB health checks.

---

## Edge Cases

- PostgreSQL is unavailable or cannot be reached.
- Executing the health check query fails even though the database connection exists.
- PostgreSQL is healthy while another dependency (Redis or Vector DB) is unavailable.
- Multiple services become unavailable at the same time, and the health endpoint should still report each dependency accurately.