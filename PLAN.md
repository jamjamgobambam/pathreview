## Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x
https://github.com/ascherj/pathreview/issues/154

### Understand
Root cause: `health_check()` in `api/routes/health.py` calls
`await db.execute("SELECT 1")` with a bare Python string. SQLAlchemy 2.x
removed implicit string-to-SQL coercion for safety reasons — literal SQL
must be explicitly wrapped in `sqlalchemy.text()`. Because `text` is
never imported in this file, the call raises an error on every request.
Confirmed via local reproduction — the server logs show:
`error="Textual SQL expression 'SELECT 1' should be explicitly declared
as text('SELECT 1')"`.

Expected behavior: `/health` should execute the query successfully and
report `"postgres": "healthy"` when the database is reachable.
Actual behavior: the query always raises, so `/health` reports
`"postgres": "unhealthy"` and returns a 503, even when Postgres is
fully up and reachable (confirmed via `docker compose ps` showing the
`db` container as healthy).

### Map
- `api/routes/health.py` — contains the buggy `execute("SELECT 1")` call
  inside `health_check()`; needs the `text` import and the query wrapped.
- `tests/unit/` — no `test_health.py` exists yet. No route-level tests
  exist in this project at all (checked `tests/unit/` and confirmed no
  `tests/integration/` folder either). I'll model my new test on
  `test_review_service.py`'s `mock_db_session` `AsyncMock` fixture
  pattern, calling `health_check()` directly as an async function rather
  than through an HTTP client, consistent with how this project tests
  service/route logic elsewhere.

### Plan
1. Import `text` from `sqlalchemy` at the top of `api/routes/health.py`.
2. Change `await db.execute("SELECT 1")` to
   `await db.execute(text("SELECT 1"))`.
3. Manually verify via `curl http://localhost:8000/health` that the
   response now reports `"postgres": "healthy"`.
4. Write `tests/unit/test_health.py`, calling `health_check()` directly
   with a mocked `db` (`AsyncMock`, following `test_review_service.py`'s
   fixture pattern) and asserting `dependencies["postgres"] == "healthy"`
   after the fix. Mock the Redis and vector_db calls as well so the test
   isolates the Postgres check specifically, rather than failing on the
   unrelated #155 Redis bug.
5. Run the full test suite (`pytest` or `make test`) to confirm nothing
   else breaks.

### Inputs & outputs
Input: an HTTP GET request to `/health`, with a live (or mocked) DB
session injected via `Depends(get_db)`.
Output: a JSON response with `"postgres": "healthy"` (and overall
`"status": "healthy"`, assuming other dependencies are also up) instead
of raising an error.

### Risks & unknowns
- Ran `grep -rn 'execute("' api/ core/` and confirmed no other raw-string
  SQL `execute()` calls exist in the project's own code — this bug is
  isolated to `health.py:31`, no sibling bugs of this type elsewhere.
- No existing `test_health.py` or route-test convention to copy exactly;
  using `test_review_service.py`'s `AsyncMock` db-session fixture as the
  closest available pattern. Risk: `health_check()` also calls out to
  Redis and vector_db checks inline within the same function, so my test
  needs to mock/isolate those too, or the test could fail on the
  unrelated #155 Redis bug (`'Settings' object has no attribute
  'redis_host'`) rather than testing my fix in isolation.
- The `import redis` and `from core.config import settings` calls happen
  inline inside the health check function rather than at module top —
  need to confirm this doesn't complicate mocking.

### Edge cases
- Postgres unreachable for a real reason (container down) — should still
  correctly report `"unhealthy"` via the existing `except Exception`
  block, not raise an unrelated error.
- Query succeeds but returns an unexpected result shape (unlikely for
  `SELECT 1`, but worth a basic assertion in the test).
- Fix must not swallow genuine DB outage exceptions — confirm the
  existing `try/except Exception` still correctly catches real failures
  after the `text()` fix is applied.

**Reproduction commit link:** https://github.com/laurale31/pathreview/commit/a57447b

**PLAN.md link:** https://github.com/laurale31/pathreview/blob/fix/154-health-check-sqlalchemy-text/PLAN.md


**Blockers or open questions:**
[we'll fill this in once we check tests/integration/ below]
