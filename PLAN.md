# Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under
SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

### Understand

**Root cause.** In `api/routes/health.py`, the PostgreSQL probe calls
`await db.execute("SELECT 1")`, passing a bare Python `str`. SQLAlchemy 2.x no
longer accepts raw textual SQL from `Connection/Session.execute()` — it must be
wrapped in `sqlalchemy.text()`. So instead of running the query, the call raises
`ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as
text('SELECT 1')`.

**Why the symptom is misleading.** That `execute` call sits inside a broad
`try/except Exception`. The `ArgumentError` (a *programming* error) is caught by
the same handler meant for *connectivity* errors, so the code sets
`dependencies["postgres"] = "unhealthy"` and flips the endpoint's overall status
to `"unhealthy"`, which returns **HTTP 503** — even though the database is fully
reachable.

**Expected vs. actual.**
- *Expected:* the probe executes `SELECT 1`; Postgres is reported `"healthy"` when
  the DB is reachable and `"unhealthy"` only when it genuinely is not.
- *Actual:* the probe never executes; Postgres is *always* reported `"unhealthy"`
  and `/health` always returns 503 for the Postgres reason.

### Map

Files/functions involved:

- **`api/routes/health.py`** — `health_check()`. The defect is the `db.execute(...)`
  call in the PostgreSQL `try` block, plus the module imports (needs `text`). **This
  is the only production file I expect to change.**
- **`tests/unit/test_health.py`** — *new file*; no tests currently exist for this
  route. This is where the regression coverage goes.
- **`core/database.py`** — `get_db()` provides the async `AsyncSession` injected via
  `Depends`. Read-only context; **no change expected**, but relevant to understand
  what `db` is.

Files I expect to touch: `api/routes/health.py`, `tests/unit/test_health.py`.

### Plan

1. **Import `text`.** Add `from sqlalchemy import text` to `api/routes/health.py`.
2. **Wrap the statement.** Change `await db.execute("SELECT 1")` to
   `await db.execute(text("SELECT 1"))`.
3. **Add regression tests** in `tests/unit/test_health.py` that call
   `health_check()` with a mocked async session and assert: (a) the statement
   passed to `execute` is a SQLAlchemy `TextClause`, not a `str`; (b) Postgres is
   reported `"healthy"` on success; (c) Postgres is still reported `"unhealthy"`
   when the query raises — so the fix cannot mask a real outage.
4. **Verify live.** With `docker compose up -d`, hit `GET /health` and confirm the
   `ArgumentError` is gone from the logs and `postgres` reports `"healthy"`.
5. **Keep the diff minimal.** Run `pytest tests/unit/test_health.py` and the full
   unit suite, and compare lint/type/test counts against `main` to confirm no new
   failures. Revert any unrelated reformatting the pre-commit hooks try to apply to
   this file (import reordering, etc.).

### Inputs & outputs

- **Input:** the async `AsyncSession` (`db`) provided by `Depends(get_db)`. The
  probe itself takes no user input.
- **Output / change in behavior:** the probe now executes successfully. On success
  it sets `dependencies["postgres"] = "healthy"`; on a real failure it sets
  `"unhealthy"` and the endpoint returns 503. The response **shape** is unchanged —
  same JSON keys — only the reported Postgres value (and the 503-vs-200 outcome for
  the Postgres reason) changes.

### Risks & unknowns

- **`/health` may still return 503 after this fix.** The same endpoint has a
  *second, independent* bug: the Redis probe reads `settings.redis_host` /
  `settings.redis_port`, which are not defined on `Settings`, raising
  `'Settings' object has no attribute 'redis_host'`. That is a separate issue and
  **out of scope for #154** — but it means "does `/health` return 200?" is the
  wrong success test. My success criterion is scoped to the **Postgres dependency
  specifically** (reports `"healthy"`; no `ArgumentError`).
- **Pre-commit / CI on pre-existing debt.** `make lint`, `make typecheck`, and
  `make test-unit` already fail on `main` (182 ruff, 559 mypy, 53 failing unit
  tests) — including 14 mypy errors in `health.py` itself, one of them the
  `redis_host` bug above. The pre-commit `mypy` hook therefore blocks a normal
  commit to this file. Unknown: whether the maintainer expects contributors to
  work around this (`--no-verify`) or whether CI will red-flag the PR for
  pre-existing issues. I'll call this out explicitly in the PR.
- **Broad `except Exception`.** The root reason a code error looked like an outage
  is the over-broad catch. Narrowing it (e.g. to connection errors) would be a more
  complete fix but expands scope; I'm treating it as a possible follow-up, not part
  of this change.

### Edge cases

- **Database genuinely down** → must still report `"unhealthy"` and 503. Covered by
  a test that makes `execute` raise.
- **Query succeeds but returns a row** → the result of `SELECT 1` is intentionally
  ignored; we only care that it executed without error. No result handling needed.
- **Session lifecycle** → `db` is managed by `get_db()`; the fix adds no new
  connection or transaction, so there's no leak or open-transaction risk.
- **Repeated calls** → `/health` is idempotent and stateless; wrapping in `text()`
  keeps it so.
