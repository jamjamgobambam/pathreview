## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand
The `GET /health` endpoint probes PostgreSQL by calling `await db.execute("SELECT 1")` with a
bare Python string. SQLAlchemy 1.x accepted this and coerced it implicitly, but SQLAlchemy 2.x
(the project pins 2.0.51) removed that coercion: `Connection.execute()` and
`AsyncSession.execute()` now require an executable construct and raise
`ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`.

Because the probe is wrapped in a broad `except Exception`, the `ArgumentError` is swallowed and
recorded as a dependency failure rather than surfacing as a crash. The endpoint therefore reports
`postgres: unhealthy` and returns HTTP 503 even when the database is fully reachable — the failure
mode is a false negative, not an outage. Any infrastructure monitor pointed at `/health` treats the
service as permanently down.

Expected behaviour: the probe succeeds against a reachable database and the endpoint returns HTTP 200
with `postgres: healthy`. Actual behaviour: the probe always raises, and the endpoint always returns 503.

### Map
Files to be modified:
* `api/routes/health.py` — the `health_check` handler containing the PostgreSQL probe.
* `tests/unit/test_health.py` — new test module; no unit tests covered this route previously.

Files inspected but deliberately not changed:
* `core/database.py` — confirmed the session is a SQLAlchemy 2.x `AsyncSession` from
  `async_sessionmaker`, which is what makes the strict-construct requirement apply.
* `core/config.py` — confirmed a separate latent bug (see Risks) that is out of scope here.

### Plan
1. **Import the `text` construct:** add `from sqlalchemy import text` to `api/routes/health.py`.
2. **Wrap the probe SQL:** change `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))`.
3. **Confirm the blast radius is one call site:** grep the codebase for other `.execute("...")`
   calls passing raw strings so the same defect isn't left elsewhere.
4. **Add a regression test module:** create `tests/unit/test_health.py` asserting the probe is called
   with a `TextClause` rather than a `str`, plus coverage of the healthy path and the 503 failure path.
5. **Prove the test is a real guard:** revert the production fix, confirm the regression test fails,
   then restore the fix and confirm it passes.

### Inputs & outputs
* **Inputs:** a `GET /health` request with an async DB session injected via `Depends(get_db)`.
* **Outputs:** HTTP 200 with `status: healthy` and `dependencies.postgres: healthy` when the database
  is reachable; HTTP 503 with `dependencies.postgres: unhealthy` only when it genuinely is not.

### Risks & unknowns
* **Broad exception handling hides the real error.** The `except Exception` around each probe means a
  programming error (like this one) is indistinguishable from a dependency outage in the response
  body. Narrowing it would improve diagnosability but changes response semantics, so it is out of
  scope for a tier-1 fix.
* **Latent second bug in the Redis probe.** `health_check` reads `settings.redis_host` and
  `settings.redis_port`, but `core/config.py` only defines `redis_url`. The Redis probe therefore
  always raises `AttributeError` and reports unhealthy. This is a separate defect from #154 and is
  left untouched; the unit tests substitute a mock settings object so the Postgres probe can be
  tested in isolation rather than papering over it in production code.
* **Pre-existing repository failures.** `make check` and `make test-unit` already fail on `main` for
  unrelated reasons, so "passing" here means introducing no new failures.

### Edge cases
* **Database genuinely unreachable:** the endpoint must still report 503 — the fix must not turn a
  real outage into a false healthy. Covered by `test_raises_503_when_postgres_probe_fails`.
* **Failing dependency correctly attributed:** the 503 body must name Postgres specifically rather
  than reporting a generic failure. Covered by `test_503_detail_reports_postgres_unhealthy`.
* **SQL text preserved:** wrapping in `text()` must not alter the statement sent to the database.
  Covered by `test_postgres_probe_executes_select_1`.
