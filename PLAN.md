# Solution plan

**Issue:** [#154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)
**Branch:** `fix/154-health-check-sql-text`
**Target PR:** end of Week 9

---

## Understand

**Root cause.** The `/health` endpoint at `api/routes/health.py:24` probes PostgreSQL with a bare Python string:

```python
await db.execute("SELECT 1")
```

SQLAlchemy 2.x no longer accepts raw strings in `AsyncSession.execute()`. It requires a `TextClause` object produced by `sqlalchemy.text(...)`. The bare string raises `ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`, which is swallowed by the surrounding `try/except` and reported as `"postgres": "unhealthy"`.

**Expected vs actual:**

- **Expected:** `GET /health` returns 200 with `dependencies.postgres == "healthy"` whenever Postgres is reachable.
- **Actual:** `GET /health` returns 503 with `dependencies.postgres == "unhealthy"` on **every** request, regardless of database state. The endpoint effectively lies about its own DB probe.

Reproduction confirmed locally (see JOURNAL.md → Week 8) — the exact SQLAlchemy 2.x error message appears in `postgres_health_check_failed` structlog output while `docker compose ps` reports the `db` container as `(healthy)`.

## Map

Files I expect to touch:

- **`api/routes/health.py`** — the endpoint containing the bug. Two changes: (1) import `text` from SQLAlchemy at the top, (2) wrap the `"SELECT 1"` argument.
- **`tests/unit/api/test_health.py`** (or the closest existing equivalent — I still need to confirm the exact path/name during Week 9 setup) — new test covering the fixed behavior. I'll model it on whatever async test pattern already exists in the `tests/` folder; PathReview has established fixture and httpx patterns to follow.

Files I'll read but likely won't modify:

- `core/database.py` — the `get_db` FastAPI dependency that produces the `AsyncSession` injected into the endpoint. I want to confirm the session type is what the docs suggest before I trust the fix.
- `api/main.py` — where the health router is registered. Only relevant if the test needs to build a test app fixture.
- Any conftest.py under `tests/` — to reuse existing async client fixtures rather than reinventing them.

## Plan

Concrete sub-tasks in the order I'll do them:

1. **Add the import.** Add `from sqlalchemy import text` near the top of `api/routes/health.py`. Alphabetize with existing SQLAlchemy imports if any.
2. **Wrap the query.** Change `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))`. Single-line diff.
3. **Verify manually.** Restart the app, `curl http://localhost:8000/health`, confirm the response is 200 with `postgres: "healthy"`, and confirm the backend log no longer emits `postgres_health_check_failed`.
4. **Locate the test module.** Find where `tests/` currently covers `api/routes/`. Read one or two existing async endpoint tests end-to-end to learn the fixture pattern (async client, DB dependency override, etc.).
5. **Write the new test.** Test that `GET /health` returns 200 and `dependencies.postgres == "healthy"` when the DB is reachable. If time permits, add a second test that uses `unittest.mock` to force the postgres probe to raise and asserts the endpoint returns 503 with `postgres: "unhealthy"` — protects against future regressions in the _other_ direction.
6. **Run project checks.** `make check` (lint + format + typecheck) and `make test-unit`. Both must pass before I open the PR.

## Inputs & outputs

**Input to the fix:** the `AsyncSession` currently injected by the `Depends(get_db)` on line 13. Nothing about the endpoint's signature changes.

**Output of the fix:**

- **Behavioral output:** `/health` now correctly reports `postgres: "healthy"` when the DB is up (the intended contract) and `postgres: "unhealthy"` only when the DB probe genuinely fails (also the intended contract). No silent lies.
- **Code output:** one added import, one wrapped call — total diff is likely 2 lines. Plus one new test file (or added tests to an existing file) covering both the healthy and unhealthy paths.

## Risks & unknowns

- **Test isolation.** PathReview's `get_db` dependency talks to the real Postgres container by default. My test needs to either (a) use that same container and rely on `db` being reachable during CI, or (b) override the dependency to a mock. I'll look at existing tests to see which convention PathReview uses before writing my own. If neither pattern is obvious, I'll ask in Slack rather than invent a new one.
- **Async event loop config.** FastAPI async endpoints under pytest need `pytest-asyncio` (or `anyio`) configured. If it isn't already set up in `tests/`, adding it is a bigger change than my issue is meant to be — in that case I'd write the test to be sync-friendly (using `TestClient` from `starlette.testclient`, which wraps async endpoints), which the project may already be doing elsewhere.
- **Pre-commit hook drift.** `make setup` installs pre-commit hooks. If my commit is refused by ruff/black/mypy on formatting I didn't cause, that's a hint the project has been through a linter version bump. Small fix, but worth budgeting time for.
- **CI failing on unrelated tests.** If `make test-unit` shows other tests already failing on main (unlikely but possible given the codebase is used for teaching), I need to distinguish "my change broke this" from "this was already broken before I touched it." Approach: run `make test-unit` before starting any code change to capture a baseline.

## Edge cases

The fix has to keep working across these:

- **Postgres is up, connection pool is healthy** — the primary success case. My test covers this.
- **Postgres container is stopped/unreachable** — the probe should raise (`OperationalError` or similar), be caught by the existing `try/except`, and correctly report `"unhealthy"`. This is what the endpoint _already_ does correctly, but I need to make sure my fix doesn't accidentally break it.
- **Postgres is up but has a permissions issue** for the app user — same handling as the "unreachable" case. The `try/except` catches any `Exception`.
- **Malformed `DATABASE_URL` in `.env`** — the FastAPI app either won't start at all (SQLAlchemy fails at engine creation) or the connection will fail on first use. Either way, that's outside the endpoint's control; my fix doesn't need to handle it.
- **Concurrent requests to `/health`.** The endpoint uses a per-request async session. My change doesn't introduce any new shared state, so no new concurrency concerns.

## Out of scope

The same endpoint has a **separate** bug: `settings.redis_host` and `settings.redis_port` don't exist on the `Settings` class, so the redis probe always fails with `'Settings' object has no attribute 'redis_host'`. This is issue #155 (a different ticket, being claimed and fixed by other contributors). My PR will not touch the redis probe — anyone reviewing my diff should see the postgres probe becoming honest while the redis probe continues to be broken. That is intentional and correct scoping for #154.
