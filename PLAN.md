## Solution plan

**Issue:** #154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x https://github.com/ascherj/pathreview/issues/154

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
In this case, the behavior expected was that api/routes/health.py runs await db.execute("SELECT 1") to check whether Postgres is reachable, which would return a successful message saying that the db connection is healthy. However, it does not behave that way, the root cause is that the health check's Postgres probe uses a raw SQL string (`"SELECT 1"`) on line 31, but the version of SQLAlchemy used in this project requires raw SQL to be wrapped in `sqlalchemy.text()`. This mismatch makes the query to fail, raising an ArgumentError, which then marks postgres: "unhealthy" even when Postgres is fine.



### Map
Which files, functions, or modules are involved?
Files i expect to be involved:
- api/routes/health.py: inside health_check() function, specifically in line 31. This line is the only line that needs to change for the actual fix.
- core/database.py: this file likely contains the database session setup and might need to be checked for compatibility with the new text() usage.

### Plan
What are the steps to fix this issue?
1. Confirm the exact import needed: from sqlalchemy import text.
2. Change line 31 from await db.execute("SELECT 1") to await db.execute(text("SELECT 1")).
3. Run my earlier reproduction script again, this time confirming the ArgumentError is gone and the call succeeds.
4. Manually verify by running the app in Docker (`make run`) and calling `GET /health` again, confirming `postgres` now reports "healthy".
5. Run make test-unit to confirm nothing else breaks.
6. Run make check (lint/format/typecheck) before opening the PR.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- Function I'm changing: health_check(db=Depends(get_db)) in api/routes/health.py.
Buggy behavior:
- Input: any call to GET /health with a working Postgres connection
- Output: 503, postgres: "unhealthy" (wrong — should be healthy)
Fixed behavior:
- Input: same — working Postgres connection
- Output: 200, postgres: "healthy"

### Risks & unknowns
What could go wrong? What are you still unsure about?
- I'm not 100% sure text("SELECT 1") is sufficient to fix the error, or if db.execute() needs any additional handling of the result. I'll check by running it against a real Postgres instance in Docker.
- The Redis check right below mine (line 44-45) references settings.redis_host, which doesn't exist on Settings. Since that's a separate AttributeError unrelated to my fix, I need to make sure my PR doesn't accidentally "fix" that since it's issue #155's scope.
- I'm not writing a new test for this fix right now since it's a single-line change I can verify manually, but after reading the contributing guide, I realize it expects tests for any change. My plan is to add a new test file, tests/unit/test_health.py (none currently exists for this route), before opening the PR, mocking the DB session the way tests/unit/test_review_service.py does.


### Edge cases
What inputs or states should your fix handle gracefully?
- Postgres reachable and query succeeds: should report "healthy".
- Postgres unreachable: should still correctly report "unhealthy" and in this case, my fix must not accidentally mask real failures, only stop false positives from the wrapping bug.
- Redis/Vector DB checks remain broken/unrelated: overall status may still show "unhealthy" due to #155 until that's fixed separately — worth noting in my PR description so a reviewer doesn't think my fix is incomplete.