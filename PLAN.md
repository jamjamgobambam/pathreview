## Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

### Understand
`health_check()` in `api/routes/health.py` probes Postgres connectivity with
`await db.execute("SELECT 1")` (line 31), passing a bare Python string. Under
SQLAlchemy 2.x, `AsyncSession.execute()` no longer accepts raw strings as
executable statements — textual SQL must be wrapped in `sqlalchemy.text()`.

- **Expected behavior:** the Postgres probe runs `SELECT 1` and, when the database
  is reachable, sets `dependencies.postgres = "healthy"` and returns HTTP 200.
- **Actual behavior:** `execute()` raises `sqlalchemy.exc.ArgumentError`
  ("Textual SQL expression 'SELECT 1' should be explicitly declared as
  text('SELECT 1')") during statement coercion — *before any DB round-trip*. The
  surrounding `try/except Exception` on lines 34–37 catches it, sets
  `dependencies.postgres = "unhealthy"` and `status = "unhealthy"`, and the
  endpoint returns HTTP 503 (lines 83–87) even though Postgres is up and
  reachable. The failure is an API misuse being misreported as an outage.

### Map
- **`api/routes/health.py`** — the one line to change (`await db.execute("SELECT 1")`
  at line 31). This is the only raw-string `execute()` call in the codebase
  (verified by grep; every other `execute()` in `api/`, `core/services/`, and
  `scripts/` passes a `select(...)` / prepared `stmt` construct, which is already
  2.x-correct).
- **`core/database.py`** — context only, no change. Defines the async `engine`,
  `AsyncSessionLocal` (`async_sessionmaker`), and the `get_db()` dependency that
  yields the `AsyncSession` injected into `health_check`. Confirms the session is a
  genuine SQLAlchemy 2.x `AsyncSession`, so `text()` is the correct fix.
- **`tests/unit/test_health.py`** — new reproduction test (committed this week). It
  currently asserts the *broken* behavior (`ArgumentError` raised; postgres
  reported "unhealthy"); its assertions get flipped to expect "healthy" once the
  fix lands.

### Plan
1. Import `text`: add `from sqlalchemy import text` at the top of
   `api/routes/health.py`.
2. Wrap the probe: change line 31 to `await db.execute(text("SELECT 1"))`.
3. Update `tests/unit/test_health.py`: the `ArgumentError` assertion no longer
   holds after the fix, so replace it with a test that the probe reports Postgres
   `"healthy"` when `execute()` succeeds (mock/stub `execute` to return normally),
   and keep a regression test that a *real* connection error still reports
   `"unhealthy"`.
4. Manually verify against a running Postgres: `docker compose up -d`, `make run`,
   then `curl localhost:8000/health` and confirm `dependencies.postgres` is
   `"healthy"` and the endpoint returns HTTP 200.
5. Confirm no other call sites need the same fix (grep already shows only
   `health.py`); document that check in the PR.

### Inputs & outputs
- **Input:** a live async DB session provided by the `get_db` dependency
  (`AsyncSession` from `core.database`).
- **Output:** the `health_status` dict returned by `health_check`, specifically
  `dependencies.postgres`, correctly reflecting real connectivity ("healthy" when
  the DB responds to `SELECT 1`, "unhealthy" only on a genuine connection error) —
  and the overall `status` / HTTP code (200 vs 503) derived from it — instead of
  flipping to "unhealthy" because of a SQLAlchemy API mismatch.

### Risks & unknowns
- **Other raw-string call sites:** mitigated — a repo-wide grep confirms
  `health.py:31` is the only `execute()` passed a raw string; all others use
  `select()`/`stmt`. Will re-confirm in the PR.
- **Behavior when Postgres is genuinely down:** the fix must not mask real
  outages. With `text("SELECT 1")`, an unreachable DB should raise a connection
  error (e.g. `OperationalError`), still caught and reported as "unhealthy" — this
  needs an explicit regression assertion so we don't trade one bug for another.
- **Test approach masking the fix:** the current reproduction relies on the
  ArgumentError being raised pre-connection; the post-fix test must exercise the
  success path without a real DB (stub `execute` to return normally) so it
  actually validates the `text()` wrapping rather than connectivity.

### Edge cases
- **DB genuinely unreachable:** should still report `postgres: "unhealthy"`, now
  via a real connection/operational error rather than an `ArgumentError`.
- **DB reachable but slow / query times out:** probe should surface a timeout as
  "unhealthy"; confirm no indefinite hang holds the endpoint open.
- **`get_db` fails before the `try` block:** if the dependency itself can't yield a
  session, the exception escapes `health_check` entirely (it happens during
  dependency resolution, outside the route's `try/except`) — worth noting as
  distinct from the in-probe failure this issue addresses.
