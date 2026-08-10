## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x #154](https://github.com/jamjamgobambam/pathreview/issues/154)

---

### Understand

**Root cause:** `api/routes/health.py` line 31 calls `await db.execute("SELECT 1")` with a bare Python string. SQLAlchemy 2.x enforces that all textual SQL must be explicitly wrapped with `sqlalchemy.text()`. When a raw string is passed, SQLAlchemy raises `ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`. The `except Exception` block in the health route catches this error and sets `postgres` to `"unhealthy"`, making the endpoint return HTTP 503 even when the database is fully reachable.

**Expected behavior:** The DB probe executes successfully when the database is up, and `GET /health` returns `{"status": "healthy", "dependencies": {"postgres": "healthy", ...}}`.

**Actual behavior:** The probe always raises `ArgumentError` regardless of DB state, so `postgres` is always `"unhealthy"` and the endpoint always returns 503.

---

### Map

Files involved:

| File | Role |
|---|---|
| `api/routes/health.py` (line 31) | **Primary change** — where the bare string is passed |
| `tests/unit/test_health_db_probe.py` | **New file** — reproduction test and post-fix verification |

No other files need to change. The fix is self-contained to one line in one route file.

---

### Plan

1. **Import `text` from SQLAlchemy** — add `from sqlalchemy import text` to the imports in `api/routes/health.py`.
2. **Wrap the bare string** — change `await db.execute("SELECT 1")` → `await db.execute(text("SELECT 1"))` on line 31.
3. **Verify the reproduction test now passes** — run `pytest tests/unit/test_health_db_probe.py` and confirm both test cases pass.
4. **Run the full unit test suite** — run `make test` (or `pytest tests/unit/`) to confirm no regressions.
5. **Manual smoke test** — start the stack with `docker compose up -d && make run`, call `GET /health`, and confirm the response shows `"postgres": "healthy"`.

---

### Inputs & outputs

**Input:** The async SQLAlchemy session (`db`) injected by `Depends(get_db)` into the `health_check` route handler.

**Change:** `db.execute("SELECT 1")` → `db.execute(text("SELECT 1"))`, where `text` is `sqlalchemy.text`.

**Output:** `db.execute` receives a `TextClause` object instead of a bare string, SQLAlchemy 2.x accepts it, the query runs, and `health_status["dependencies"]["postgres"]` is set to `"healthy"`.

---

### Risks & unknowns

- **SQLAlchemy version pinning:** The fix targets SQLAlchemy 2.x behavior. If `pyproject.toml` ever allows downgrading to 1.x, `text()` is still valid there too — no regression risk.
- **Other raw SQL strings in the codebase:** A quick `grep -r 'execute("SELECT'` should be run to check whether any other routes have the same pattern. (A preliminary search found no other occurrences outside `health.py`.)
- **Async session type:** The `db` session is an `AsyncSession` from SQLAlchemy's async extension. `text()` works identically with both sync and async sessions — no additional changes needed.

---

### Edge cases

- **Database is genuinely down:** After the fix, if the DB is truly unreachable (e.g., Docker container stopped), `db.execute(text("SELECT 1"))` will raise a `sqlalchemy.exc.OperationalError`. The existing `except Exception` block handles this correctly and still reports `"postgres": "unhealthy"`.
- **Database reachable but slow:** No timeout is set on the probe. This is a pre-existing limitation, not in scope for this fix.
- **`text()` already imported elsewhere:** No conflict — `sqlalchemy.text` is a standalone utility function.
