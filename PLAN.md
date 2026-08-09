## Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

### Understand

**Root cause.** In `api/routes/health.py` (line 31) the PostgreSQL probe runs
`await db.execute("SELECT 1")`, passing the query as a plain Python string.
SQLAlchemy 2.x no longer executes bare strings — textual SQL must be wrapped in
`sqlalchemy.text()`. Verified locally on SQLAlchemy 2.0.51: `execute("SELECT 1")`
raises `sqlalchemy.exc.ObjectNotExecutableError: Not an executable object:
'SELECT 1'`, while `execute(text("SELECT 1"))` returns `1` correctly.

**Expected vs. actual.**
- *Expected:* when Postgres is reachable, the probe succeeds and reports
  `postgres: "healthy"`, and `GET /health` returns HTTP 200.
- *Actual:* the probe always raises, the broad `except Exception` marks
  `postgres: "unhealthy"`, the overall status flips to `unhealthy`, and the
  endpoint returns HTTP 503 — even when the database is fully up. Confirmed by
  hitting `GET /health` locally: 503 with `"postgres": "unhealthy"` while the
  Docker `db` container reported healthy.

### Map

Modules/files involved:
- **`api/routes/health.py`** — contains the bug (`health_check()`, line 31) and
  the broad `try/except`. **Primary file I will change.**
- **`tests/unit/test_health_check.py`** — my reproduction test (added in Week 8).
  **I will extend this** with a test that asserts the Postgres probe reports
  healthy after the fix.
- `core/database.py` — defines `get_db()` and the async `AsyncSession`. Reference
  only, to understand what `db` is; **no change needed**.
- `core/config.py` — `Settings`. Reference only; relevant to the *separate* #155
  bug, which I must not touch.

**Files I expect to touch:** `api/routes/health.py`, `tests/unit/test_health_check.py`.

### Plan

1. **Add the import.** At the top of `api/routes/health.py`, add
   `from sqlalchemy import text`.
2. **Fix the probe.** Change `await db.execute("SELECT 1")` to
   `await db.execute(text("SELECT 1"))` (line 31). Leave the surrounding
   `try/except` intact so genuine DB outages are still reported.
3. **Add a regression test.** Extend `tests/unit/test_health_check.py` with a
   test that drives the Postgres probe and asserts it reports
   `postgres: "healthy"` when the database is reachable, using a dependency
   override so the test does not depend on a live Postgres.
4. **Verify locally.** Run `make check && make test-unit`; all lint, type, and
   unit checks must pass.
5. **Confirm end-to-end.** With services up, `curl localhost:8000/health` and
   confirm the `postgres` dependency now reports `"healthy"`.

### Inputs & outputs

- **Input:** an async SQLAlchemy `AsyncSession` (`db`) yielded by `get_db()`, and
  a reachable PostgreSQL instance.
- **Output / change:** the probe executes `text("SELECT 1")` successfully and
  sets `health_status["dependencies"]["postgres"] = "healthy"`. When all
  dependencies are healthy, `GET /health` returns HTTP 200 instead of 503. No
  API schema change, no new response fields, no new dependencies.

### Risks & unknowns

- **Scope collision with #155 (same file).** `api/routes/health.py` also has a
  separate bug in the Redis block (`settings.redis_host` / `settings.redis_port`
  don't exist on `Settings`, ~lines 44–45), which independently causes a 503.
  Risk: my change accidentally touches the Redis block, or my endpoint test
  asserts a full 200 (which would still fail because of #155). Mitigation: change
  only the Postgres line, and assert specifically on the `postgres` dependency
  value rather than the overall status code.
- **Async testing approach is undecided.** `aiosqlite` is not installed, so I
  can't spin up an in-memory async DB. I'll either use a FastAPI dependency
  override with a stub/real async session, or an integration test against the
  local Postgres. Need to pick one in Week 9.
- **Broad `except Exception` masks errors.** It swallows the specific exception,
  so I must verify the fix by confirming the probe no longer enters the `except`
  branch (probe returns "healthy"), not just that no error is printed.

### Edge cases

- **Database genuinely down / unreachable:** the probe must still report
  `postgres: "unhealthy"` and the endpoint must still return 503 — the fix must
  not swallow real failures, so the `try/except` stays.
- **Missing/incorrect import:** if `text` isn't imported, the code raises
  `NameError`; the import must be added alongside the change.
- **No regression to other probes:** the Redis (#155) and vector-DB checks must
  behave exactly as before — my change is limited to the Postgres line.
- **Trivial result handling:** `SELECT 1` returns a single scalar; the fix only
  needs the statement to execute, so it must not assume a particular row shape.
