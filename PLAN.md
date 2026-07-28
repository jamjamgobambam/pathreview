## Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

### Understand
The `GET /health` handler probes PostgreSQL by running
`await db.execute("SELECT 1")` (`api/routes/health.py:31`). SQLAlchemy 2.x no
longer accepts a bare string as an executable — it must be wrapped in
`sqlalchemy.text()`. During statement coercion the raw string raises
`ArgumentError`, which the `except Exception` block catches and reports as
`postgres: "unhealthy"`, flipping the overall status to `unhealthy` and
returning `503`.

- **Expected:** With a reachable database, `GET /health` returns `200` and
  `postgres: "healthy"`.
- **Actual:** Even with a healthy, reachable database, the probe raises
  `ArgumentError`, so `GET /health` returns `503` with `postgres: "unhealthy"`.

The root cause is the SQLAlchemy 1.x → 2.x API change: textual SQL must be
declared explicitly via `text()`.

### Map
- `api/routes/health.py` — the health handler; **the one line to fix** is the
  Postgres probe on line 31. Needs `from sqlalchemy import text` added.
- `tests/unit/test_health_probe.py` — reproduction test (added in Week 8);
  will be expanded to assert the fixed behavior.
- `core/database.py` — provides the `get_db` async session dependency; read-only
  reference, no change expected.

### Plan
1. Add `from sqlalchemy import text` to `api/routes/health.py`.
2. Change the probe from `await db.execute("SELECT 1")` to
   `await db.execute(text("SELECT 1"))`.
3. Add/verify a test asserting that with a working session the probe returns a
   row and `postgres` is reported `healthy` (extend `test_health_probe.py`, and
   ideally a route-level test that `GET /health` reports postgres healthy).
4. Run the full unit suite + manual `curl http://localhost:8000/health` to
   confirm `200` / `postgres: healthy`.
5. Update JOURNAL.md and open the PR.

### Inputs & outputs
- **Input:** an async DB session from `get_db` (a live Postgres connection in
  production; SQLite in tests).
- **Output:** the probe executes `SELECT 1` successfully and the handler reports
  `postgres: "healthy"`; `GET /health` returns `200` when all dependencies are
  up. No schema, migration, or API-contract changes.

### Risks & unknowns
- Low risk — a one-line change on an isolated code path.
- The reproduction test uses a **sync** SQLite connection because the
  `ArgumentError` originates in SQLAlchemy's statement coercion (identical
  sync/async) and `aiosqlite` is not installed. A route-level async test would
  need `aiosqlite` (or mocking `get_db`); decide in Week 9 whether to add the
  dependency or mock.
- Confirm no other call sites pass raw SQL strings (Redis/vector-DB probes are
  unaffected; they don't touch SQLAlchemy).

### Edge cases
- Database genuinely down/unreachable → probe should still raise and correctly
  report `postgres: "unhealthy"` (the fix must not swallow real failures).
- Other dependencies (Redis, vector DB) down while Postgres is healthy → overall
  status still `unhealthy`, but `postgres` should now read `healthy`.
