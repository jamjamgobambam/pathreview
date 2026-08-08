# Solution plan

**Issue:** #154 — Health check DB probe passes a raw SQL string, which fails
under SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

- **Tier:** 1 (labels: `api`, `bug`, `good first issue`, `tier-1`)
- **Branch:** `fix/154-health-db-probe-text`
- **Contributor:** Harsh Mehta (fork: `Harsh05dev/pathreview`)

## Understand

**What needs to change:** the PostgreSQL probe inside the `GET /health`
endpoint. It currently executes the raw string `"SELECT 1"`.

**Expected vs. actual.** When PostgreSQL is reachable, `/health` should report
`dependencies.postgres == "healthy"` and return HTTP `200`. Instead it reports
`"unhealthy"` and returns HTTP `503` on every call.

**Root cause.** `health_check()` calls `await db.execute("SELECT 1")` with a
bare `str`. SQLAlchemy 2.0 removed implicit conversion of plain strings into
executable text clauses (deprecated in 1.4, removed in 2.0). The project pins
`sqlalchemy>=2.0.0` (installed: `2.0.51`), so the call raises
`ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared
as text('SELECT 1')`. That error is swallowed by the surrounding broad
`try/except Exception`, which flips Postgres to `"unhealthy"` and the overall
status to `"unhealthy"`, forcing a `503`. Net effect: a permanent false outage
for any monitor/load balancer polling `/health`, even when the DB is up.

**Confirmed reproduced** — see `tests/unit/test_health_repro.py` and the Week 8
JOURNAL entry.

## Map

Files/functions I expect to touch:

- `api/routes/health.py` — `health_check()`, line 31:
  `await db.execute("SELECT 1")`. This is the one behavioral change. I will also
  add `from sqlalchemy import text` at the top of this file.
- `tests/unit/test_health.py` — **new** file. The Week 9 fix test asserting the
  probe now succeeds and passes a `TextClause`. Modeled on the async-mock +
  `@pytest.mark.unit`/`@pytest.mark.asyncio` pattern already used by sibling
  tests in `tests/unit/` (strict `pytest-asyncio` mode).
- `tests/unit/test_health_repro.py` — **exists** (Week 8 reproduction). Will be
  removed or folded into `test_health.py` once the fix test replaces it.

Files I have checked and will NOT touch:
- `core/database.py` — `get_db` dependency; unchanged, only consumed.
- `pyproject.toml` — SQLAlchemy already pinned `>=2.0.0`; no dep change needed.

## Plan

Concrete, ordered sub-tasks:

1. Run `make test-unit` on a clean branch first to record a green baseline
   before touching anything.
2. Add `from sqlalchemy import text` to the imports in `api/routes/health.py`.
3. Change line 31 in `health_check()` from `await db.execute("SELECT 1")` to
   `await db.execute(text("SELECT 1"))`. No other logic in the handler changes.
4. Write `tests/unit/test_health.py`: mock the async session, assert the happy
   path sets `dependencies.postgres == "healthy"` and returns `200`, and assert
   `db.execute` is called with a `sqlalchemy.sql.elements.TextClause`
   (regression guard against re-introducing a raw string). Add a DB-error path
   asserting `"unhealthy"` + `503` still works.
5. Remove `tests/unit/test_health_repro.py` (Week 8 scaffold now superseded).
6. Run `make test-unit`, then `make check` (ruff + black + mypy); fix any
   findings until both are clean.
7. Commit as `fix(api): wrap health check DB probe in text()` and open a PR
   against `ascherj/pathreview` with the template filled and `Fixes #154`.

## Inputs & outputs

**Function changed:** `health_check(db=Depends(get_db)) -> dict` in
`api/routes/health.py`. Its public signature and return schema do **not**
change — only the SQL statement type handed to the DB driver changes.

- **Input consumed:** an async SQLAlchemy session (`db`). The probe statement
  changes from `str` `"SELECT 1"` → `TextClause` `text("SELECT 1")`.
- **Output — before (bug):** with a healthy DB, `execute()` raises
  `ArgumentError`; response body `dependencies.postgres == "unhealthy"`,
  `status == "unhealthy"`, HTTP `503`.
- **Output — after (fix):** with a healthy DB, `execute()` succeeds;
  `dependencies.postgres == "healthy"`, and — if Redis/vector DB are also up —
  `status == "healthy"`, HTTP `200`. The DB-down path is unchanged: still
  `"unhealthy"` + `503`.

## Risks & unknowns

1. **`get_db` session type mismatch.** The fix assumes the injected session is a
   SQLAlchemy 2.x `AsyncSession` whose `execute()` accepts a `TextClause`. Risk:
   if `core/database.py` yields some wrapper, `text()` may still fail. Mitigation:
   read `core/database.py` `get_db` before finalizing and confirm the session
   type in Step 3.
2. **Other probes on the same endpoint stay red.** Redis probe references
   `settings.redis_host`, and the vector-DB probe reads `settings.vector_db_url`
   — if those attributes are missing on `Settings` (see nearby issue #155), the
   overall `/health` status can still be `"unhealthy"` even after my Postgres
   fix, making a full `200` hard to demonstrate locally. Mitigation: my
   `test_health.py` will mock/isolate the Postgres path and assert on
   `dependencies.postgres` specifically, not the aggregate status. #155 is out
   of scope for this PR.
3. **Async test wiring.** `pytest-asyncio` runs in strict mode here, so the new
   test in `tests/unit/test_health.py` needs an explicit `@pytest.mark.asyncio`;
   forgetting it silently skips. Mitigation: mirror the reproduction test, which
   is already confirmed passing.

## Edge cases

- **Healthy DB, healthy Redis + vector DB** → `postgres == "healthy"`, aggregate
  `"healthy"`, HTTP `200` (the primary fixed path).
- **Healthy DB, but Redis or vector DB down** → `postgres == "healthy"` while
  aggregate stays `"unhealthy"` + `503`. The Postgres fix must not be masked by
  unrelated failing probes; the test asserts the Postgres key independently.
- **DB genuinely unreachable** (connection error, not a type error) → the
  `try/except` must still catch it and report `postgres == "unhealthy"` + `503`.
  The fix must not swallow real outages.
- **`execute()` returns but the result is unused** → the probe only needs the
  call to not raise; the returned rows are irrelevant. Test asserts the call
  happened with a `TextClause`, not on the returned value.
