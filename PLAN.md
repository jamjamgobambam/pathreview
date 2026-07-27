## Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

### Understand
Root cause: in `api/routes/health.py`, the PostgreSQL probe runs the raw string
`await db.execute("SELECT 1")` (line 31). SQLAlchemy 2.x no longer accepts a
plain string here — textual SQL must be wrapped in `sqlalchemy.text()`. So the
call raises `ArgumentError: Textual SQL expression 'SELECT 1' should be
explicitly declared as text('SELECT 1')`. That error is caught by the
surrounding `except Exception` (line 34), which marks postgres as `"unhealthy"`.

- Expected: when Postgres is reachable, `/health` reports `postgres: "healthy"`.
- Actual: `/health` reports `postgres: "unhealthy"` and returns 503, even though
  `docker ps` shows the Postgres container `Up (healthy)` on port 5433.

### Map
Files / functions involved:
- `api/routes/health.py` → `health_check()` — the actual fix.
  - line 31: `await db.execute("SELECT 1")` → needs `text()` wrapping.
  - top of file: add `from sqlalchemy import text` to imports.
- `core/database.py` → `get_db` / `AsyncSessionLocal` — context only (the async
  session type is what enforces the SQLAlchemy 2.x rule). No change needed.
- `tests/integration/test_health_check.py` (new) — add a test using a live
  session that asserts the postgres dependency is `"healthy"`.

### Plan
1. Add `from sqlalchemy import text` to the imports in `api/routes/health.py`.
2. Change the probe to `await db.execute(text("SELECT 1"))` (line 31).
3. Add an integration test that calls `health_check` with a live
   `AsyncSessionLocal` session and asserts `dependencies["postgres"] == "healthy"`
   (reading it from the 503 detail, since redis/#155 keeps overall status down).
4. Run `make check` (lint + format + type) and `make test-unit`, then hit
   `GET /health` and confirm postgres is now reported healthy.
5. Keep the change scoped to the postgres probe only — do not touch the redis
   probe (that is issue #155).

### Inputs & outputs
- Input: `health_check()` receives a live `AsyncSession` via `Depends(get_db)`.
- Change: the DB probe passes a `text()`-wrapped statement instead of a raw
  string.
- Output: the probe executes successfully when the DB is reachable, so
  `dependencies.postgres == "healthy"`; the endpoint returns 200 when the other
  dependencies are also healthy.

### Risks & unknowns
- Over-reach risk: the broad `except Exception` (line 34) also hides genuine
  DB-down cases, but fixing that is a separate concern — I will only wrap the
  statement in `text()` and leave the error handling as is.
- Redis (#155) still breaks the overall status, so `/health` may keep returning
  503 after my fix. My test must assert on the `postgres` field specifically,
  not on overall status 200.
- Unknown — CI/DB availability: does the project's CI run integration tests
  against a live Postgres? Investigation path: check `.github/workflows/` and
  `docs/CONTRIBUTING.md` before relying on an integration test.
- Confirm the correct import is `from sqlalchemy import text` (not from a
  submodule) for this SQLAlchemy version.

### Edge cases
- Postgres genuinely down: the probe should still raise, get caught, and report
  `"unhealthy"` — this correct behavior must be preserved after the fix.
- Postgres reachable but query returns unexpected rows: `SELECT 1` is a trivial
  liveness check, so the result value is not inspected — no change needed.
- Only the postgres probe is modified; the redis and vector_db probes stay
  untouched.
