# Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under
SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

### Understand

**Root cause.** In `api/routes/health.py`, the PostgreSQL liveness probe calls
`await db.execute("SELECT 1")`, passing a bare Python string. SQLAlchemy 2.x
removed the implicit conversion of plain strings into executable statements, so
`AsyncSession.execute()` now rejects a raw string and raises
`sqlalchemy.exc.ArgumentError: Textual SQL expression 'SELECT 1' should be
explicitly declared as text('SELECT 1')`.

**Expected vs. actual.**
- *Expected:* with a reachable database, the probe succeeds and `/health`
  reports `postgres: "healthy"`.
- *Actual:* the probe throws `ArgumentError`; the handler's broad
  `except Exception` swallows it, sets `postgres: "unhealthy"` and the overall
  `status: "unhealthy"`, and the endpoint returns **HTTP 503** even though
  PostgreSQL is up — a false-negative outage that would page on-call and fail
  readiness checks in a deploy.

### Map

Files / functions involved:
- **`api/routes/health.py`** → `health_check()`, specifically the imports and
  the `# Check PostgreSQL` block. **Primary change.**
- `core/database.py` → `get_db` provides the `AsyncSession` injected via
  `Depends`. Context only; no change expected.
- **`tests/unit/test_health.py`** → no health tests exist today; add one.

Files I expect to touch: `api/routes/health.py`, `tests/unit/test_health.py`.

### Plan

1. **Import the construct** — add `from sqlalchemy import text` to
   `api/routes/health.py`.
2. **Wrap the query** — change `await db.execute("SELECT 1")` to
   `await db.execute(text("SELECT 1"))`.
3. **Add unit tests** in `tests/unit/test_health.py` following the repo's
   `@pytest.mark.unit` / `@pytest.mark.asyncio` + `AsyncMock` conventions:
   (a) a regression guard asserting the probe passes a SQLAlchemy `TextClause`
   rather than a `str`; (b) the healthy path; (c) the failure path reports
   `unhealthy` without crashing.
4. **Verify** — run `pytest tests/unit/test_health.py -v`, then confirm live:
   `GET http://localhost:8000/health` should flip `postgres` from
   `"unhealthy"` to `"healthy"` against the running stack.
5. **Hold scope to #154** — do not touch the sibling Redis bug in the same file
   (`settings.redis_host`, issue #155); it belongs to a separate contributor.

### Inputs & outputs

- **Input:** an async SQLAlchemy session (`db`) from `Depends(get_db)`; the
  probe issues a trivial `SELECT 1` liveness query and does not read rows.
- **Output / change:** the probe executes a valid `TextClause`; on success
  `health_status["dependencies"]["postgres"]` becomes `"healthy"`. When every
  dependency is healthy the endpoint returns 200. No schema, response-shape,
  data, or public-API changes.

### Risks & unknowns

- **Broad `except Exception` masks a sibling bug.** The same handler also fails
  on `settings.redis_host` (issue #155), so even after my fix `/health` may
  still return 503 overall (redis `unhealthy`). Reviewers expecting a green
  `/health` need to know postgres is fixed independently of redis.
- **Repo-wide CI is pre-red.** `ruff check .`, `black --check .`, and `mypy`
  fail on pre-existing seeded bugs — including `redis_host` in *this* file — so
  a #154-scoped change cannot make the whole file pass `mypy` without poaching
  #155. Plan: call this out explicitly in the PR notes.
- **Unknown — preferred idiom.** Maintainers might prefer `sqlalchemy.select(1)`
  over `text("SELECT 1")`. I'm going with `text("SELECT 1")` as the minimal fix
  that matches the issue's wording and the error message's suggestion.

### Edge cases

- **Database genuinely down / connection refused** → the probe must still be
  caught and report `postgres: "unhealthy"` (covered by test (c)).
- **Unconsumed result object** → we never read rows, so a returned result that
  isn't iterated must not raise; only execution matters.
- **No stray transaction state** → `SELECT 1` is read-only and needs no commit;
  the fix must not leave an open transaction on the shared session.
- **Exact SQL text** → `text("SELECT 1")` must stringify to exactly
  `"SELECT 1"` (asserted in the test) with no accidental parameter binding.
