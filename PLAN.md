## Solution plan

**Issue:** [#154 - Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand
**Root cause:** In `api/routes/health.py`, the Postgres check calls `await db.execute("SELECT 1")`, passing a raw Python string. SQLAlchemy 2.x's async engine requires textual SQL to be explicitly wrapped in `sqlalchemy.text()`. Passing a bare string raises an `ArgumentError` at execution time.

**Expected behavior:** When Postgres is reachable, the `/health` endpoint should report `"postgres": "healthy"` and return a 200 status.

**Actual behavior:** Even when Postgres is up and reachable, the `db.execute("SELECT 1")` call raises an `ArgumentError`. This false negative causes the endpoint to log `postgres_health_check_failed` and report `"postgres":"unhealthy"`, `"status": "unhealthy"`, and return a `503 Service Unavailable`.

### Map
Files I expect to touch:
- `api/routes/health.py` - `health_check()` function (line ~ ): where the bare string is passed via `db.execute("SELECT 1")`. I will wrap the text in `sqlalchemy.text()`.

I don't expect to interact with other files. 

### Plan
1. Import `text` from `sqlalchemy` in `api/routes/health.py`.
2. Replace `await db.execute("SELECT 1")` with `await db.execute(text("SELECT 1"))`.
3. Manually verify the fix by running the app and hitting `GET /health` with the DB stack up to confirm `"postgres": "healthy"` and a `200` response.

### Inputs & outputs
**Function I'm changing:** `health_check(db=Depends(get_db)) -> dict`

**Existing (buggy) path:**
- Input: a live `AsyncSession` connected to a reachable Postgres instance
- Actual output: raises `ArgumentError` internally, so the endpoint returns `{"status": "unhealthy", "dependencies": {"postgres": "unhealthy", ...}}` with a `503 Service Unavailable` even though Postgres is up.

**New behavior (fixed):**
- Input: a live `AsyncSession` connected to a reachable Postgres instance
- Expected output: `db.execute(text("SELECT 1"))` succeeds → `health_status["dependencies"]["postgres"] = "healthy"` → endpoint returns `200` with `{"status": "healthy", "dependencies": {"postgres": "healthy", ...}}` (assuming redis/vector_db also healthy)
- Does NOT change behavior when Postgres is genuinely unreachable — should still catch the connection error and report `"unhealthy"` / `503`.

### Risks & unknowns
- If other parts of the codebase also call `.execute()` with raw strings, the same bug could exist elsewhere and go unnoticed until specifically tested.
- Whether there's an existing test suite covering `/health`. This fix could regress silently again in the future without an added test. I will look for tests and see about potentially adding one to cover this bug.

### Edge cases
- **Postgres genuinely down/unreachable:** The fixed code should still correctly catch the connection error and report `"unhealthy"`.
- **Query succeeds but returns unexpected data:** Not a concern here since the check only cares that the query executes without raising.
- **Session/connection pool exhausted:** Should still be caught by the existing `try/except Exception` and reported as `"unhealthy"` rather than raising an unhandled 500.
