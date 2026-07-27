## Solution plan

**Issue:** [#154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand
The Postgres probe in `health_check()` runs `await db.execute("SELECT 1")`, passing a bare Python string as the SQL statement. SQLAlchemy 2.x's `AsyncSession.execute()` only accepts an `Executable` (e.g. the result of `sqlalchemy.text(...)`) or an ORM construct — a bare string raises `sqlalchemy.exc.ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`.

That exception is caught by the surrounding `try/except Exception`, which marks `dependencies.postgres = "unhealthy"` and sets overall `status = "unhealthy"`. So the probe never actually tests connectivity — it fails identically whether Postgres is up or down.

- **Expected:** when the DB is reachable, `dependencies.postgres == "healthy"` and `/health` returns 200.
- **Actual:** `dependencies.postgres` is always `"unhealthy"` (confirmed locally against a working SQLite session, see Reproduction below), and `/health` always returns 503 for the Postgres leg regardless of real DB state.

### Map
- `api/routes/health.py` — line 31, the `await db.execute("SELECT 1")` call inside the Postgres try/except block. This is the only line that needs to change (wrap in `sqlalchemy.text("SELECT 1")`, plus a `from sqlalchemy import text` import).
- `tests/integration/test_health_check.py` — new reproduction test added this week; will be updated once the fix lands so it asserts `"healthy"` instead of `"unhealthy"`.
- `core/database.py` — read for context (engine/session setup); no changes expected here.
- `core/config.py` — noted a separate, out-of-scope bug: `health.py` references `settings.redis_host` / `settings.redis_port`, but `Settings` only defines `redis_url`. This means the Redis leg of the probe currently always fails too (`AttributeError`, caught and reported as "unhealthy"). Not part of #154's scope, but it means `/health` will still return 503 overall even after the Postgres fix, purely because of the Redis leg — worth flagging in the PR description so it isn't mistaken for an incomplete fix.

### Plan
1. Add `from sqlalchemy import text` to `api/routes/health.py` and change `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))`.
2. Update `tests/integration/test_health_check.py`'s assertion from `"unhealthy"` to `"healthy"` for the Postgres dependency, since the probe should now succeed against a working session.
3. Add a second, narrow assertion/test (or extend the existing one) verifying no exception/log entry is produced for the Postgres leg specifically, so a future regression back to a bare string is caught immediately.
4. Run `pytest tests/integration/test_health_check.py -v` and the existing unit suite to confirm no regressions.
5. Manually hit `GET /health` against the docker-compose Postgres to visually confirm the JSON body reports `postgres: healthy` (Redis/vector_db may still show unhealthy/unavailable due to the separate config bug noted above — expected, not a regression).

### Inputs & outputs
- **Input:** an `AsyncSession` (real or test) passed into `health_check(db=...)` via FastAPI's `Depends(get_db)`.
- **Output:** the `health_status` dict / JSON body, specifically `dependencies.postgres` flipping from always-`"unhealthy"` to accurately reflecting the DB connection's real state (`"healthy"` when reachable, `"unhealthy"` only on a genuine connection failure).

### Risks & unknowns
- **Masked Redis bug:** as noted above, `settings.redis_host`/`settings.redis_port` don't exist on `Settings` (`core/config.py`), so the overall `/health` status will likely stay `"unhealthy"`/503 even after this fix, purely from the Redis leg throwing `AttributeError`. Need to decide (with reviewer input) whether to fix that in the same PR or file it as a separate follow-up issue — currently leaning toward a separate issue since it's out of scope for #154's title.
- **Test environment:** the full `make setup` / Docker Postgres stack wasn't available in this environment, so reproduction and the added test use an in-memory SQLite `AsyncSession` instead of real Postgres. Need to confirm the fix behaves identically against asyncpg/Postgres before considering this fully verified (`tests/integration` are tagged as requiring Docker services per `pyproject.toml`'s pytest markers).
- **`db.execute` return-value assumptions:** confirm nothing downstream inspects the return value of this specific `execute()` call expecting the old (broken) behavior — a quick grep shows the result is currently discarded, so this looks low-risk.

### Edge cases
- DB genuinely unreachable (wrong host/port/credentials) — probe should still correctly report `"unhealthy"` after the fix, not just always-healthy.
- Session already closed/invalid when `health_check` runs — should still be caught by the existing `try/except Exception` and reported as `"unhealthy"`, not raise an unhandled error.
- Slow/hanging DB connection — out of scope for this fix (no timeout currently implemented on the probe); worth a note but not a blocker for #154.
