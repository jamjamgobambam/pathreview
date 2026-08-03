## Solution plan

**Issue:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x
**Link:** https://github.com/ascherj/pathreview/issues/154

### Understand

**Root cause:**
SQLAlchemy 2.x no longer accepts raw SQL strings passed directly to `execute()`. Raw strings must be explicitly wrapped in `text()` from the sqlalchemy module.

**Expected behavior:**
- Health check endpoint (`GET /health`) returns HTTP 200
- All dependencies (postgres, redis, vector_db) report as "healthy"
- Response includes timestamp and safety events count

**Actual behavior:**
- Health check endpoint returns HTTP 503 Service Unavailable
- PostgreSQL dependency marked as "unhealthy"
- Error thrown: `CompileError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`

**Evidence:**
Confirmed with SQLAlchemy 2.0.51 installed locally.

---

### Map

**Files to touch:**
- `api/routes/health.py` (main file with the issue)

**Specific location:**
- Function: `health_check()` (lines 9-73)
- Problem line: 32 - `await db.execute("SELECT 1")`

**Related imports:**
- Currently missing: `from sqlalchemy import text` (or `from sqlalchemy.sql import text`)

---

### Plan

**Steps to fix this issue:**

1. **Import `text` function**
   - Add `from sqlalchemy import text` at the top of `api/routes/health.py`

2. **Wrap the raw SQL string**
   - Change line 32 from: `await db.execute("SELECT 1")`
   - Change to: `await db.execute(text("SELECT 1"))`

3. **Test the fix locally**
   - Run `make run` to start the backend
   - Call `GET http://localhost:8000/health` 
   - Verify response is 200 (not 503)
   - Verify `postgres` dependency is "healthy"

4. **Verify no other raw SQL strings exist**
   - Search codebase for other instances of `db.execute("` to catch similar issues
   - If found, apply the same fix

5. **Commit and push**
   - Commit the fix with a clear message
   - Push to the branch `fix/154-healthcheck-SQL-string`

---

### Inputs & outputs

**Input:**
Raw SQL string: `"SELECT 1"`

**Output:**
SQLAlchemy text-wrapped expression: `text("SELECT 1")`

**What changes:**
- Health check will successfully execute the SQL query
- PostgreSQL health check will pass (assuming DB is running)
- Health endpoint will return 200 instead of 503

---

### Risks & unknowns

**Potential risks & how to verify:**

1. **Other raw SQL strings in codebase**
   - Action: Run `grep -r 'db.execute("' api/` to find all instances
   - If found: List them and apply the same `text()` wrapper fix
   - Files to check: `api/`, `core/`, `rag/`, `ingestion/`

2. **Redis health check also failing**
   - Action: Verify if this is a separate configuration issue
   - Check: `docker compose ps` to confirm Redis container is running
   - Not blocking this fix but should be documented

3. **Test coverage for health endpoint**
   - Action: Check if `tests/` directory has health check tests
   - If not: Will create one to verify the fix works

---

### Edge cases

**How to handle gracefully:**

1. **Database is actually down**
   - Test: Stop Docker containers (`docker compose down`), call `/health`, verify it reports 503
   - Expected: The `text()` wrapper doesn't mask real errors—exception caught, status stays "unhealthy" ✓

2. **Multiple dependency failures**
   - Test: With postgres up but redis down, health check should return 503 and show only postgres as healthy
   - Expected: Endpoint correctly aggregates dependency status ✓

3. **SQL query variations**
   - Verify: `SELECT 1` is the simplest possible query—should work on all postgres versions
   - No special handling needed ✓