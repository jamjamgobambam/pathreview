## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand
`api/routes/health.py` checks Postgres connectivity with `await db.execute("SELECT 1")`, passing a bare Python string. `db` is a SQLAlchemy 2.x async `AsyncSession` (`core/database.py`), and 2.x's `execute()` only accepts an `Executable` construct — a raw string raises `sqlalchemy.exc.ObjectNotExecutableError: Not an executable object: 'SELECT 1'`. That exception is caught by the broad `except Exception` on line 34, which marks `postgres` as `"unhealthy"` and flips the whole response to a 503.

Expected behavior: the probe should run `SELECT 1` and report `postgres: "healthy"` whenever Postgres is actually reachable, only reporting `"unhealthy"` on a genuine connection failure.
Actual behavior: the probe always fails and reports `"unhealthy"`/503, regardless of whether Postgres is up, because the exception is a syntax/type error, not a connectivity error.

### Map
- `api/routes/health.py` — the only file that needs a code change: import `text` from `sqlalchemy` and wrap the query as `text("SELECT 1")`.
- `core/database.py` — read-only reference to confirm `db` is an `AsyncSession` and confirm no other raw-string queries exist here (none found).
- `tests/integration/` — no existing health-check test; add one here to cover this route with a real (or mocked) `AsyncSession`.

### Plan
1. In `api/routes/health.py`, add `from sqlalchemy import text` and change `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))`.
2. Search the codebase for any other `db.execute("...")` call sites with a raw string (e.g. `grep -rn "db.execute(\"" `) to make sure this isn't a repeated pattern elsewhere.
3. Run the app locally (`make run`) with Postgres up and confirm `curl -i http://localhost:8000/health` now returns `200` with `postgres: "healthy"`.
4. Add a regression test in `tests/integration/` that hits `GET /health` against a real/test Postgres connection and asserts `postgres == "healthy"` and status `200`, so this can't silently regress.
5. Optionally, verify the failure path is still correct by pointing the app at a bad `DATABASE_URL` and confirming the endpoint still reports `postgres: "unhealthy"`/503 for an actual outage (distinguishing "real down" from "bad query shape" was the whole point of the bug).

### Inputs & outputs
- Input: an HTTP `GET /health` request; the `db` `AsyncSession` from the `get_db` dependency.
- Output: unchanged JSON shape (`status`, `dependencies.postgres`, etc.) — only the *correctness* of the `postgres` value changes, from always-`"unhealthy"` to reflecting the real connection state.

### Risks & unknowns
- Need to confirm no other code path constructs `db.execute()` with a raw string that would hit the same 2.x incompatibility (Redis and vector DB checks in the same file don't use `db.execute`, so they're unaffected).
- Unsure whether CI has a Postgres service available for an integration test, or whether the regression test needs to mock `db.execute` instead — will check `.github/workflows/ci.yml` before writing the test.
- `pool_pre_ping=True` is already set on the engine (`core/database.py`), so a genuinely dead connection should still surface as a real error after the fix — want to double check this isn't masked once the query itself is valid.

### Edge cases
- Postgres reachable, query valid → `postgres: "healthy"`, 200 overall (assuming Redis/vector DB also healthy).
- Postgres actually down/unreachable → `postgres: "unhealthy"`, 503 overall (must still work after the fix — this is the case the current bug conflates with the false positive).
- Postgres reachable but slow/timing out → should still surface as `"unhealthy"` via the existing `except Exception`, not hang indefinitely (out of scope to change timeout behavior, but worth confirming it isn't newly broken).
