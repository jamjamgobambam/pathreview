# Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x  
https://github.com/ascherj/pathreview/issues/154

## Understand

The issue occurs in the `/health` endpoint's PostgreSQL health check. The endpoint currently executes the query `"SELECT 1"` directly using SQLAlchemy's database session. In SQLAlchemy 2.x, raw SQL strings must be explicitly wrapped using `text()`, causing the health check to incorrectly mark PostgreSQL as unhealthy even when the database connection is available.

The expected behavior is that the database probe successfully executes and the `/health` endpoint reports PostgreSQL as healthy.

## Map

Files involved:

- `api/routes/health.py` — contains the `/health` endpoint and PostgreSQL database probe
- Health check related tests (if present) — may need updates to verify the corrected behavior

## Plan

1. Update the database health probe in `api/routes/health.py` to import and use SQLAlchemy's `text()` function.
2. Run the health endpoint locally to verify that the PostgreSQL dependency reports as healthy after the change.
3. Review and update existing health check tests to ensure the expected behavior is covered.
4. Run relevant checks/tests before opening the pull request.

## Inputs & outputs

Input:
- The database session provided through FastAPI dependency injection.

Output:
- A successful SQL execution using SQLAlchemy's supported textual SQL format.
- The `/health` endpoint correctly reports PostgreSQL availability.

## Risks & unknowns

- Existing tests may mock database execution and may need adjustment after changing the SQL query format.
- The health endpoint contains multiple dependency checks, so unrelated failures should not be accidentally modified.
- Need to confirm whether there are existing tests specifically covering the PostgreSQL probe.

## Edge cases

- PostgreSQL is unavailable or unreachable.
- The database session raises an exception during execution.
- The health endpoint should still return an unhealthy status when the database genuinely fails.