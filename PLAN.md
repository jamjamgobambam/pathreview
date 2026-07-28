## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand
The health check route in `api/routes/health.py` verifies Postgres connectivity
by executing the raw string `"SELECT 1"` via `db.execute()`. SQLAlchemy 2.x
removed implicit string-to-SQL coercion for safety reasons — raw SQL must be
explicitly wrapped in `sqlalchemy.text()`. Because the string is passed bare,
`db.execute()` raises an `ArgumentError` on every call. Expected behavior:
the probe should run `SELECT 1` successfully and report `"postgres": "healthy"`
when the database is reachable. Actual behavior: the probe always throws,
so postgres is reported `"unhealthy"` regardless of actual DB state.

### Map
- `api/routes/health.py` - contains the `health_check()` route handler and the
  broken `db.execute("SELECT 1")` call (the core fix location)
- `core/database.py` - defines `get_db()`, the dependency that provides the
  SQLAlchemy async session used in the health check
- `core/config.py` - defines `Settings`, referenced elsewhere in the same
  health check function (relevant to the separate redis issue, #155, not this fix)

### Plan
1. Import `text` from `sqlalchemy` at the top of `api/routes/health.py`
2. Wrap the raw SQL string: change `db.execute("SELECT 1")` to
   `db.execute(text("SELECT 1"))`
3. Add type annotations (`dict[str, Any]` return type, `Any` on the `db`
   parameter) to satisfy `mypy`/`ruff` pre-commit checks that surfaced once
   the file was modified
4. Manually verify the fix by reverting temporarily, reproducing the original
   error, then restoring the fix and confirming `"postgres": "healthy"` via
   `curl http://localhost:8000/health`
5. Document reproduction steps and outcome in `JOURNAL.md`

### Inputs & outputs
- **Input:** an active SQLAlchemy async `Session`/`Connection` object (`db`),
  injected via FastAPI's `Depends(get_db)`
- **Output (before fix):** an unhandled `ArgumentError` caught by the
  surrounding `try/except`, causing `"postgres": "unhealthy"` in the
  JSON response and an overall `503 Service Unavailable`
  ![alt text](image-1.png)
- **Output (after fix):** a successful `SELECT 1` query execution, resulting
  in `"postgres": "healthy"` in the JSON response
  ![alt text](image.png)

### Risks & unknowns
- The `try/except Exception` block in `health_check()` silently swallows the
  real error and converts it into a generic `"unhealthy"` status. This made
  initial diagnosis harder, since the JSON response alone didn't show the
  underlying `ArgumentError` (only the server logs did)
- The endpoint's overall `"status"` field aggregates all three dependency
  checks (postgres, redis, vector_db), so even after this fix, `/health`
  still returns `503` overall because of the unrelated `redis_host` bug in
  the same file (issue #155) — need to make clear in the PR description that
  this is expected and out of scope
- No existing test file (`tests/unit/test_health.py` does not exist), so
  there's no existing test coverage to regress against; will rely on manual
  verification via `curl` unless a test is added in Week 9

### Edge cases
- **Database temporarily unreachable** (e.g., Docker container stopped): the
  fixed code should still correctly report `"postgres": "unhealthy"` in this
  case — the fix must not accidentally mask real outages, only correct the
  false-positive caused by the raw-string bug
- **Concurrent requests to `/health`** while the DB connection pool is under
  load: the fix should not introduce new connection-handling issues, since
  `text()` wrapping is purely a query-declaration change and does not alter
  connection/session lifecycle