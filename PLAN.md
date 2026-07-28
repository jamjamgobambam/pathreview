## Solution plan

**Issue:** [#154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand

The `GET /health` endpoint is supposed to report whether Postgres, Redis, and
the vector DB are reachable. The Postgres probe in
[api/routes/health.py:31](api/routes/health.py#L31) calls:

```python
await db.execute("SELECT 1")
```

SQLAlchemy 2.x's `Connection.execute()` / `AsyncSession.execute()` only
accepts `Executable` objects (e.g. `text("SELECT 1")`, a `Core`/`ORM`
construct) — it rejects plain strings outright with
`ObjectNotExecutableError` (a subclass of `ArgumentError`), before the query
is ever sent to the database.

`health.py`'s `try/except Exception` (lines 29-37) catches that error,
logs it, and sets `dependencies.postgres = "unhealthy"` and
`status = "unhealthy"`, which makes the route return `503` (line 83-87).

- **Expected behavior:** when Postgres is reachable, `GET /health` reports
  `dependencies.postgres: "healthy"`.
- **Actual behavior:** `dependencies.postgres` is always `"unhealthy"`,
  regardless of whether Postgres is actually up, because the probe itself is
  malformed — it never reaches the database.

I confirmed this locally (see reproduction section below): with the real
Postgres container healthy and reachable, `/health` still returns `503` with
`postgres: "unhealthy"`, and the server log shows the exact SQLAlchemy error
being swallowed:

```
postgres_health_check_failed error="Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')"
```

**Reproduction:**
1. `docker compose up -d db redis vector-db` (all three become healthy)
2. `uvicorn api.main:app --port 8000`
3. `curl http://localhost:8000/health` → `503`, `dependencies.postgres: "unhealthy"`
4. `tests/unit/test_health_check.py` isolates the same failure
   (`ObjectNotExecutableError`) against a plain SQLAlchemy engine, without
   needing the full stack, and confirms `text("SELECT 1")` fixes it.

### Map

- **`api/routes/health.py`** — the file with the bug. `health_check()`
  (lines 12-89), specifically the Postgres try block at lines 29-37. Needs
  a `from sqlalchemy import text` import and `db.execute(text("SELECT 1"))`.
- **`core/database.py`** — defines `get_db()` / `AsyncSessionLocal`, the
  `AsyncSession` dependency injected into `health_check`. Not changed, but
  worth reading to confirm `db` is a real `AsyncSession` (it is) and that
  `execute()` there follows the same 2.x `Executable`-only contract.
- **`tests/unit/test_health_check.py`** — reproduction test I already added;
  will extend with an integration-style test once `health.py` is fixed
  (see sub-tasks below).
- **`docs/API.md`** — documents `GET /health`; check whether its example
  response needs updating once the fix changes what a healthy response
  looks like (it currently doesn't show example payloads, so likely no
  change needed, but worth a read).

### Plan

1. **Fix the probe.** In `api/routes/health.py`, add `from sqlalchemy import
   text` and change line 31 to `await db.execute(text("SELECT 1"))`.
2. **Add a route-level regression test.** Add a test (likely
   `tests/integration/test_health.py`, since it needs a real or fixture-backed
   `AsyncSession`) that calls the `/health` endpoint with a working DB
   dependency override and asserts `dependencies.postgres == "healthy"` —
   this is the test that would have caught #154 before it shipped, and it's
   different from the unit-level reproduction test already in
   `tests/unit/test_health_check.py`.
3. **Verify locally against the real stack.** Re-run
   `docker compose up -d db redis vector-db` + `uvicorn api.main:app`, hit
   `/health`, and confirm `dependencies.postgres` flips to `"healthy"`.
4. **Run the full check suite.** `make lint`, `make typecheck`, `make
   test-unit`, `make test-integration` to make sure the import and change
   don't break anything else (e.g. mypy's `disallow_untyped_defs`, ruff's
   import-sort rule `I` in `pyproject.toml`).
5. **Update PR description / CHANGELOG-equivalent** noting the fix and, if
   relevant, flag the unrelated `redis_host`/`redis_port` `AttributeError`
   (see Risks) as a follow-up issue rather than silently fixing it here.

### Inputs & outputs

- **Input:** none from the caller's perspective — `GET /health` takes no
  parameters. The relevant "input" is the runtime state of the Postgres
  connection (up/down/misconfigured), which the probe is supposed to detect.
- **Output change:** `health_status["dependencies"]["postgres"]` will
  correctly resolve to `"healthy"` when Postgres is reachable (currently
  always `"unhealthy"`). No change to the response schema/shape — only to
  which value it's allowed to take. HTTP status code on a fully-healthy
  system moves from `503` to `200` (assuming the unrelated Redis issue below
  is also addressed, otherwise it stays `503` for a different reason).

### Risks & unknowns

- **Redis probe is separately broken and will mask verification.**
  `api/routes/health.py:44-46` reads `settings.redis_host` /
  `settings.redis_port`, but `core/config.py:12` only defines
  `redis_url: str`. This raises `AttributeError`, caught by the same
  broad `except Exception`, so `dependencies.redis` is always
  `"unhealthy"` too — confirmed in my local repro
  (`error="'Settings' object has no attribute 'redis_host'"`). After
  fixing the Postgres probe, `/health` will still return `503` overall
  because of this *separate, out-of-scope* bug. I need to verify success
  by checking `dependencies.postgres` specifically, not the overall
  `status`/HTTP code, and should flag this as a follow-up issue rather
  than scope-creeping #154 to fix it too.
- **Broad `except Exception` blocks hide root causes.** The same pattern
  that let #154 go unnoticed (catch-log-mark-unhealthy) applies to all
  three dependency checks. Fixing just the Postgres line doesn't address
  the underlying observability gap — worth a mention in the PR but not
  necessarily in scope for this fix.
- **Session vs. connection-level `execute`.** `db` in `health_check` is an
  `AsyncSession` (from `core/database.py`'s `get_db`), not a raw
  `Connection`. Need to confirm `AsyncSession.execute(text(...))` returns a
  `Result` the same way `Connection.execute()` does for `.scalar()`/no-op
  usage — I believe it does (same 2.x unified `execute()` API), but should
  double check with a quick script before/while writing the integration
  test.
- **CI/test environment may not have Postgres available**, which would make
  the new integration test in `tests/integration/` a "requires Docker
  services" test per the `integration` marker in `pyproject.toml` — need to
  check `tests/conftest.py` / CI config for how integration tests get a DB
  fixture, or whether an `AsyncMock` override of `get_db` is the expected
  pattern instead (the existing `tests/integration/__init__.py` is empty, so
  there's no existing pattern to follow yet).

### Edge cases

- **Postgres reachable but query legitimately fails** (e.g. permissions
  issue, DB in recovery mode) — should still report `"unhealthy"` with the
  real error logged, not swallow it silently. The fix shouldn't change this
  behavior, only stop it from firing on a healthy DB.
- **Postgres unreachable** (container down, wrong port) — after the fix,
  this should still correctly resolve to `"unhealthy"` via a real
  connection-level exception (e.g. `OSError`/`ConnectionRefusedError`
  wrapped by SQLAlchemy), not the `ArgumentError` we're fixing. Need to test
  both "DB down" and "DB up" paths, not just the up path.
- **Redis and vector DB down while Postgres is up** — `health_status` should
  still report Postgres as `"healthy"` independently, since each dependency
  is checked and recorded in its own `try` block. Confirms the fix is scoped
  correctly and doesn't accidentally make the endpoint all-or-nothing.
- **Concurrent requests to `/health`** — each request gets its own
  `AsyncSession` via `Depends(get_db)`, so no shared-state issue, but worth
  a sanity check that the fixed probe doesn't leak connections under load
  (pool is `pool_size=10, max_overflow=20` per `core/database.py`).
