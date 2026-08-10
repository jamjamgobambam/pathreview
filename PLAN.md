## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x #154](https://github.com/ascherj/pathreview/issues/154)

### Understand

**Root cause:** `api/routes/health.py` calls `await db.execute("SELECT 1")` with a plain Python string. SQLAlchemy 2.x enforces that all textual SQL must be wrapped in `sqlalchemy.text()` — passing a bare string raises `ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`. The exception is caught by the broad `except Exception` block, so the endpoint silently marks Postgres as "unhealthy" and returns HTTP 503, even when the database is perfectly reachable.

**Expected behavior:** `GET /health` returns `{"status": "healthy", "dependencies": {"postgres": "healthy", ...}}` with HTTP 200 when the database is up.

**Actual behavior:** The probe always fails with `postgres: "unhealthy"` and HTTP 503 because the raw string is rejected before the query ever reaches the database.

### Map

Files to change:
- `api/routes/health.py` — the only file with the broken `db.execute("SELECT 1")` call (line 30)

Files to add/update:
- `tests/unit/test_health.py` — new unit tests reproducing the bug and verifying the fix

Files read for context (no changes needed):
- `core/database.py` — confirms `db` is an `AsyncSession` from SQLAlchemy's async API
- `core/config.py` — checked that `redis_host`, `redis_port`, and `vector_db_url` exist on `Settings`

### Plan

1. **Add `text` import** — add `from sqlalchemy import text` to the imports in `api/routes/health.py`.
2. **Wrap the SQL literal** — change `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))` on the single offending line.
3. **Write a failing test first** — in `tests/unit/test_health.py`, add `test_health_check_db_probe_fails_with_raw_string` that mocks `db.execute` to raise the same `ArgumentError` SQLAlchemy 2.x raises, confirming the route returns 503 with `postgres: "unhealthy"`.
4. **Write the passing test** — add `test_health_check_db_probe_passes_with_text_wrapper` that mocks a successful `db.execute` and asserts the call argument is a `sqlalchemy.text` object, not a plain string.
5. **Run `make check && make test-unit`** — confirm linter, type checker, and all tests pass before opening the PR.

### Inputs & outputs

**Input:** The `health_check` route handler receives an `AsyncSession` injected by FastAPI's `Depends(get_db)`.

**Change at the call site:**
- Before: `await db.execute("SELECT 1")` — argument type `str`
- After: `await db.execute(text("SELECT 1"))` — argument type `sqlalchemy.sql.elements.TextClause`

**Output:** No change to the HTTP response shape. A healthy database now correctly returns `{"dependencies": {"postgres": "healthy"}, "status": "healthy"}` with HTTP 200 instead of 503.

### Risks & unknowns

- **Other raw SQL strings in the codebase:** A quick grep shows `db.execute("SELECT 1")` appears only in `api/routes/health.py`. No other files need changes, but worth verifying with `grep -r 'db.execute("' .` before opening the PR.
- **Async session API compatibility:** `AsyncSession.execute()` accepts `text()` objects in SQLAlchemy 1.4+ and 2.x. The fix is backwards-compatible and does not require any engine or session config changes.
- **Test isolation for Redis and vector DB checks:** The unit tests mock `redis.Redis` and `core.config.settings` to avoid live dependency calls. If those patches need adjustment for CI, the mock paths may need updating to match wherever `redis` and `settings` are imported inside the function.

### Edge cases

- **Database is genuinely down:** After the fix, a real connection failure (e.g., Postgres not running) should still be caught by the `except Exception` block and correctly report `postgres: "unhealthy"`. The `text()` wrapper must not swallow real errors.
- **`db` session is `None` or already closed:** If `get_db` yields a closed or invalid session, `db.execute(text("SELECT 1"))` should raise and the except block should handle it gracefully — same behavior as before the fix.
- **SQLAlchemy version below 2.x:** On SQLAlchemy 1.4 (legacy), `text()` is still accepted; the fix does not break older environments.
