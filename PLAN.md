## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

https://github.com/YugynDprodigy10/pathreview/commit/ea436cf292959fc6597f10e7d725d71ffbb76415
---

### Understand

**Root cause:** Line 22 of `api/routes/health.py` calls `await db.execute("SELECT 1")` — passing a raw Python string to SQLAlchemy's `execute()`. SQLAlchemy 2.x enforces that all textual SQL must be explicitly wrapped in `sqlalchemy.text()`. Passing a bare string raises `ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`. This causes the PostgreSQL health check to fail and report the database as `"unhealthy"` even when it is fully reachable.

**Expected behavior:** `GET /health` returns `200` with `"postgres": "healthy"` when the database is up.

**Actual behavior:** `GET /health` catches the `ArgumentError` in the `except` block, sets `"postgres": "unhealthy"`, and returns `503 Service Unavailable`.

---

### Map

**Files to touch:**

| File | Change |
|---|---|
| `api/routes/health.py` | Add `from sqlalchemy import text` import; wrap `"SELECT 1"` in `text()` |

**Files to read (no changes needed):**

| File | Why |
|---|---|
| `core/database.py` | Understand what `get_db` yields — confirms `db` is an AsyncSession |
| `tests/unit/api/test_health.py` | Understand existing test structure to verify fix passes |

---

### Plan

1. **Open `api/routes/health.py`** and locate line 22: `await db.execute("SELECT 1")`

2. **Add the import** at the top of the file:
   ```python
   from sqlalchemy import text
   ```

3. **Wrap the raw string** in `text()`:
   ```python
   await db.execute(text("SELECT 1"))
   ```

4. **Run the existing tests** to confirm the fix doesn't break anything:
   ```bash
   pytest tests/unit/api/test_health.py -v
   ```

5. **Commit with a conventional message** following `CONTRIBUTING.md`:
   ```
   fix(health): wrap SQL probe in sqlalchemy.text() for SQLAlchemy 2.x
   ```

---

### Inputs & outputs

**Input:** The `db` session injected by `get_db` dependency — an `AsyncSession` from SQLAlchemy 2.x.

**Change:** `await db.execute("SELECT 1")` → `await db.execute(text("SELECT 1"))`

**Output:** The PostgreSQL probe executes successfully, `health_status["dependencies"]["postgres"]` is set to `"healthy"`, and `GET /health` returns `200` when the database is reachable.

---

### Risks & unknowns

- **Import conflict:** `text` is a common name — need to confirm nothing else in `health.py` shadows it. Looking at the current imports (`fastapi`, `structlog`, `datetime`, `core.database`), there is no conflict.

- **AsyncSession compatibility:** `text()` is the correct wrapper for both sync and async SQLAlchemy 2.x sessions. No additional changes needed for async usage.

- **Other raw SQL strings:** A project-wide search for other bare `execute("` calls might reveal similar issues elsewhere, but those are out of scope for this fix.

- **Test coverage:** If `tests/unit/api/test_health.py` mocks the database session, the test may not exercise the actual `execute()` call. Need to inspect the test file to confirm the fix is validated by tests.

---

### Edge cases

- **Database genuinely down:** The fix should not change behavior when the database is actually unreachable — the `except` block should still catch real connection errors and correctly report `"unhealthy"`.

- **`text()` import already present:** If a future refactor adds `text` elsewhere in the file, the import is idempotent — no risk of duplication.

- **Empty string or None:** Not applicable — `text("SELECT 1")` is a constant, not user input.