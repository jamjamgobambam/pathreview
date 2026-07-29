Solution plan
Issue: Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x — https://github.com/ascherj/pathreview/issues/154

Understand
The /health endpoint probes Postgres with await db.execute("SELECT 1")in api/routes/health.py (line 25). SQLAlchemy 2.x no longer accepts barestrings for textual SQL — they must be wrapped in sqlalchemy.text(). Sothe probe raises ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1'), the handler's except blockcatches it, marks Postgres unhealthy, sets overall status unhealthy,and the route returns HTTP 503.

Expected: when Postgres is reachable, /health reportspostgres: healthy and returns 200 (assuming Redis and vector DB also OK).
Actual: /health returns 503 with postgres: unhealthy even whenPostgres is up, because the probe throws before it can succeed.
Confirmed locally: pytest tests/unit/test_health_route.py shows the rawstring raises ArgumentError, and curl localhost:8000/health returns 503.

Map
api/routes/health.py — line 25 await db.execute("SELECT 1") (the bug);imports at top need from sqlalchemy import text added.
tests/unit/test_health_route.py — new reproduction test (already added);after the fix, expand it to a route-level test asserting 200 + healthy.
tests/conftest.py — currently only has resume/README fixtures; may needan async DB session fixture for the route-level test in Week 9.
Scan only: grep -rn '\.execute("' api/ core/ to confirm no other bareSQL strings exist elsewhere; if any do, note them as out of scope.
Plan
Add from sqlalchemy import text to the imports in api/routes/health.py.
Replace await db.execute("SELECT 1") withawait db.execute(text("SELECT 1")) on line 25.
Expand tests/unit/test_health_route.py with a route-level test thatstubs get_db with an in-memory async session and asserts the responseis 200 and dependencies.postgres == "healthy".
Re-run curl localhost:8000/health locally and confirm 200 + healthy.
Run pytest plus the repo's lint/typecheck (make lint / make typecheckper the Makefile) to confirm nothing else breaks.
Inputs & outputs
Input: a GET /health request (with the stack running and Postgres up).
Output: HTTP 200 with{"status": "healthy", "dependencies": {"postgres": "healthy", ...}}instead of 503. Internally, db.execute() now receives a TextClauseinstead of a str, so it no longer raises.
Risks & unknowns
Other bare-SQL call sites: the fix is local to health.py, but a grepmay surface similar patterns elsewhere in api/ or core/. Those are outof scope for #154; I'll list them in the PR description rather than fixthem here. Investigation path: grep -rn '\.execute("' api/ core/.
Test DB choice: the reproduction uses in-memory SQLite, but the realprobe runs against Postgres. text("SELECT 1") is dialect-agnostic, sobehavior should match — worth confirming with the live endpoint in step 4.
Async fixture plumbing: the route uses Depends(get_db). Overridingthe dependency in tests requires a working async session fixture, whichtests/conftest.py doesn't currently provide — may need to add one, oruse FastAPI's dependency_overrides.
Redis/vector DB in route test: the route also probes Redis andvector_db; the route-level test must stub or skip those so they don'tmask the Postgres assertion.
Edge cases
Postgres genuinely down → handler should still catch the exception andreport unhealthy (the except block already does this; the fix mustnot swallow real connection errors).
Redis or vector DB down while Postgres up → route still returns 503because overall status follows any unhealthy dependency; Postgres justshouldn't be the false-negative anymore.
text() return type: db.execute(text("SELECT 1")) returns aCursorResult; the current code doesn't read the result, so no furtherchange needed — but worth confirming no downstream code expects a scalar.
