# Solution Plan

**Issue:** Health check DB probe should use SQLAlchemy text()

**Issue link:** https://github.com/ascherj/pathreview/issues/154

---

## Understand

The application's health check verifies that PostgreSQL is available by executing a simple `SELECT 1` query. The current implementation passes this query directly to SQLAlchemy as a plain Python string. SQLAlchemy 2.x requires textual SQL statements to be wrapped using `text()`. Because of this, the health check may incorrectly report PostgreSQL as unavailable even when the database is running normally.

---

## Map

### Files involved

- `api/routes/health.py`
- Health check tests (if available)
- `JOURNAL.md`

---

## Plan

1. Reproduce the issue using the `/health` endpoint and verify that PostgreSQL is reported as unhealthy even when the Docker container is healthy.
2. Locate the PostgreSQL health check implementation in `api/routes/health.py`.
3. Replace the raw SQL string with SQLAlchemy's `text()` function.
4. Verify that the health endpoint correctly reports PostgreSQL as healthy after the change.
5. Run existing tests (or update/add a health check test if necessary) to ensure the fix works correctly.

---

## Inputs & Outputs

### Input

- GET `/health`
- PostgreSQL database connection
- SQLAlchemy session

### Output

- PostgreSQL health status is reported correctly.
- SQLAlchemy 2.x compatibility is restored.
- The health endpoint accurately reflects database availability.

---

## Risks & Unknowns

- Confirm that `text()` is the only required SQLAlchemy change.
- Determine whether automated tests already cover the health endpoint.
- Ensure the change does not affect Redis or Vector DB health checks.

---

## Edge Cases

- PostgreSQL is unavailable.
- SQL execution fails.
- PostgreSQL is healthy while another dependency is unhealthy.
- Multiple services fail simultaneously.