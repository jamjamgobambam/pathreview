## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x — #154](https://github.com/ascherj/pathreview/issues/154)

### Understand

The PostgreSQL health probe in `api/routes/health.py` calls:

```python
await db.execute("SELECT 1")
```

SQLAlchemy 2.x does not allow textual SQL to be passed directly as a plain string to `AsyncSession.execute()`. Textual SQL must be explicitly declared using `sqlalchemy.text()`.

The expected behavior is that the health route successfully executes a lightweight `SELECT 1` query and reports PostgreSQL as `"healthy"` when the database is reachable.

The actual behavior is that SQLAlchemy raises an `ArgumentError`, the route catches the exception, PostgreSQL is marked as `"unhealthy"`, and the endpoint returns `503 Service Unavailable`.

### Map

The primary file involved is:

* `api/routes/health.py`

  * `health_check()`
  * PostgreSQL probe at `await db.execute("SELECT 1")`

Files to investigate for existing testing conventions:

* `tests/`
* Any existing health-route or API-route test files
* `core/database.py`, to understand the database session dependency returned by `get_db`

Files I expect to modify:

* `api/routes/health.py`
* An existing health-check test file, or a new test file under `tests/` if no health-route tests currently exist

Documentation files for Week 8:

* `JOURNAL.md`
* `PLAN.md`

### Plan

1. Confirm the reproduction by starting the local services, calling `GET http://localhost:8000/health`, and recording that PostgreSQL is reported as `"unhealthy"` even though its Docker container is healthy.

2. Inspect `api/routes/health.py`, `core/database.py`, and the existing test suite to understand how database sessions and FastAPI dependencies are tested in this project.

3. Import `text` from SQLAlchemy and replace the raw SQL execution with:

   ```python
   await db.execute(text("SELECT 1"))
   ```

4. Add or update a focused test that verifies the PostgreSQL probe passes a SQLAlchemy textual statement to the database session and reports PostgreSQL as healthy when execution succeeds.

5. Run the relevant test file, then run the broader project checks to confirm that formatting, linting, typing, and existing tests still pass.

6. Call the `/health` endpoint again and verify that the PostgreSQL dependency is no longer marked unhealthy because of the raw SQL string error.

### Inputs & outputs

**Input:**

* An asynchronous SQLAlchemy database session provided by the `get_db` FastAPI dependency
* A request to `GET /health`
* A reachable or unreachable PostgreSQL database

**Expected output when PostgreSQL is reachable:**

* The `SELECT 1` probe executes without a SQLAlchemy `ArgumentError`
* `health_status["dependencies"]["postgres"]` is set to `"healthy"`

**Expected output when PostgreSQL is unavailable:**

* The database exception is caught
* PostgreSQL is reported as `"unhealthy"`
* The endpoint returns `503 Service Unavailable`

The change should affect only how the textual PostgreSQL probe is constructed. It should not change Redis, vector database, or safety-event behavior.

### Risks & unknowns

* There may not currently be a dedicated test for the health route, so I may need to determine the project’s preferred location and style for API route tests.
* Tests may need to override the `get_db` dependency or use an `AsyncMock` database session to avoid requiring a live PostgreSQL connection.
* The endpoint can still return `503` when Redis or another critical dependency is unhealthy, even after the PostgreSQL probe is fixed. Therefore, validation must inspect the PostgreSQL dependency status rather than relying only on the overall HTTP status.
* Import ordering and typing rules must continue to satisfy Ruff, Black, and mypy.
* The Redis health failure observed during reproduction appears separate from issue #154 and should not be included in this fix.

### Edge cases

* PostgreSQL is reachable and the query executes successfully.
* PostgreSQL is unavailable or the session raises a connection-related exception.
* The database session raises an unexpected SQLAlchemy exception.
* PostgreSQL is healthy while Redis is unhealthy; the endpoint may still return `503`, but PostgreSQL should remain marked `"healthy"`.
* Redis and PostgreSQL are both healthy; the endpoint should report both dependencies accurately.
* The fix must continue using an asynchronous database session and must not introduce a synchronous database call.
