## Solution plan

**Issue:** Database health probe fails with `ArgumentError` because raw SQL string isn't wrapped in `text()` — (https://github.com/ascherj/pathreview/issues/154)

### Understand

**Root cause:** `api/routes/health.py` executes a literal Python string, `"SELECT 1"`, directly against the SQLAlchemy session/connection (e.g. `session.execute("SELECT 1")`). SQLAlchemy 1.x implicitly coerced bare strings into textual SQL clauses, so this worked. SQLAlchemy 2.x removed that implicit coercion — `execute()` now only accepts executable constructs (`select()`, `text()`, ORM statements, etc.), not plain strings. Passing a raw string raises:

```
sqlalchemy.exc.ArgumentError: Textual SQL expression 'SELECT 1' should be
explicitly declared as text('SELECT 1')
```

**Expected behavior:** `GET /health` should report `"database": "up"` (or equivalent) whenever the database is reachable.

**Actual behavior:** The probe raises `ArgumentError` on every call. That exception is caught by a broad `try/except` in the health check (intended to catch real connectivity failures) and reported as `"database": "down"` — even when the database is completely healthy. It's a false negative caused by an API mismatch, not an actual outage, and it's currently indistinguishable from a real DB failure because the exception is swallowed rather than logged.

### Map

Files/functions expected to be touched:
- `api/routes/health.py` — the route handler and/or helper function (e.g. `check_database()`) containing the raw `"SELECT 1"` call. This needs the `text()` import and wrapper.
- `api/tests/` (or wherever the test suite lives) — add/extend a test that calls the health route against a live/test DB session and asserts the DB check reports healthy.
- Possibly other modules with the same pattern — need to grep the codebase for `.execute("` to check whether this bug exists in more than one place (e.g. a shared DB utility module, other probes, migrations scripts run at startup).

### Plan

1. **Reproduce and document**: confirm the `ArgumentError` locally by calling `GET /health` (or invoking the route/helper directly in a test) with a live DB session, and capture the traceback.
2. **Grep the codebase** for other bare-string `.execute()` calls (`grep -rn '\.execute("' api/`) to scope whether this is a single-line fix or needs to be applied in multiple places.
3. **Apply the fix**: import `text` from `sqlalchemy` in `api/routes/health.py` and wrap the literal query as `session.execute(text("SELECT 1"))` (and in any async equivalent, keep the `await`).
4. **Tighten error handling**: make sure the `except` block around the probe logs the exception (rather than silently swallowing it) so a similar regression is visible in logs next time, instead of just flipping a status flag with no trace.
5. **Add a regression test** that runs the health route against a test DB session and asserts the database check reports "up", so this can't silently reappear.

### Inputs & outputs

- **Input:** an HTTP `GET /health` request (or a direct unit-test call into the route handler) with a live/test SQLAlchemy session.
- **Output before fix:** health response reporting `"database": "down"` due to a swallowed `ArgumentError`, and a hidden traceback in logs (or nothing, if the exception is silently caught).
- **Output after fix:** health response reporting `"database": "up"` when the DB is reachable, and a real `"down"` status (with logged exception) only for genuine connectivity failures.

### Risks & unknowns

- Unsure whether `api/routes/health.py` uses a sync `Session` or an `AsyncSession` — the fix is the same (`text()`), but the surrounding `await`/session-management code needs to be read carefully before editing.
- The same bare-string `.execute()` pattern might exist in other files (other health/readiness probes, startup scripts, migration helpers) — need to grep broadly rather than assuming this is the only occurrence.
- The current broad `except Exception` around the probe may be masking other, unrelated errors beyond this one — tightening it could surface issues that were previously hidden, so I'll want to check CI/logs after the fix, not just locally.
- Need to confirm which SQLAlchemy version is pinned in `requirements.txt`/`pyproject.toml` to make sure this is in fact a 1.x→2.x behavior change and not something else version-specific.

### Edge cases

- Database temporarily unreachable (real outage) — health check should still correctly report "down" and not be masked by this fix.
- Async vs sync session usage — the wrapped `text()` call must still be awaited correctly if the session is async.
- Other raw-SQL call sites elsewhere in the codebase using the same unwrapped-string pattern — should be caught by the grep step, not left for a future bug report.
- Health check timeout behavior — confirm that fixing the false failure doesn't change timeout/latency handling around the probe.
