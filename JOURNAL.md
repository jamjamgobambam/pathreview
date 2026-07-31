## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The database health check in `api/routes/health.py` calls
`db.execute("SELECT 1")` with a bare SQL string. SQLAlchemy 2.x requires
literal SQL to be explicitly wrapped in `sqlalchemy.text()` before
execution, so this call raises an `ArgumentError` instead of running the
query. As a result, the `/health` endpoint reports the database as
unhealthy even when Postgres is fully reachable, which is misleading for
anyone or any monitoring tool relying on that endpoint. A successful fix
imports `text` from `sqlalchemy` and wraps the query string, so the probe
executes correctly and `/health` reflects the database's true status.

**Selection notes:**
I chose Tier 1 since this is my first time contributing to a large,
unfamiliar codebase. I confirmed the bug directly by opening
`api/routes/health.py` and reading the `health_check()` function in full:
the Postgres check calls `db.execute("SELECT 1")` with no `text` import
anywhere in the file, matching the issue exactly. No `test_health.py`
exists yet in `tests/unit/`, so I'll be writing the first test for this
route, modeled on the test conventions used elsewhere in the project. I
also noticed this same file contains a second, unrelated known bug
(#155, an invalid `settings.redis_host` reference in the Redis check
block) — I'm not touching that, but it confirms I read the whole
function, not just the one line I'm fixing. The fix itself is a one-line
change plus one new test, comfortably within the 3–6 hour Tier 1 estimate
for Weeks 8–9. No blockers or open dependencies were found on the issue.


**Branch name:** fix/154-health-check-sqlalchemy-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction summary:**
Ran the app locally with `make run` (Postgres and Redis containers
confirmed healthy via `docker compose ps`). Called `GET /health` via
curl and observed a 503 response with `"postgres":"unhealthy"`. Server
logs confirmed the exact root cause:
`error="Textual SQL expression 'SELECT 1' should be explicitly declared
as text('SELECT 1')"`. The logs also show a separate, unrelated error
(`'Settings' object has no attribute 'redis_host'`, issue #155) in the
Redis check — confirming my issue is isolated to the Postgres check only.
**Reproduction commit link:** https://github.com/laurale31/pathreview/commit/a57447b

**PLAN.md link:** https://github.com/laurale31/pathreview/blob/fix/154-health-check-sqlalchemy-text/PLAN.md

**Blockers or open questions:**
No route-level test conventions exist yet in this project (tests/integration/
exists but is empty, and tests/unit/ has no test_health.py). Planning to
model my Week 9 test on test_review_service.py's AsyncMock db-session
fixture pattern instead, calling health_check() directly rather than
through an HTTP client.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed PLAN.md sub-tasks 1–3: added the `text` import to
`api/routes/health.py` and wrapped the `SELECT 1` query in `text()`.
Verified via curl that `/health` now reports `"postgres": "healthy"`
instead of raising the SQLAlchemy `ArgumentError`. Confirmed via a
`git stash` comparison that existing ruff/mypy issues in `health.py`
(1 ruff error, 11 mypy errors) predate my change and aren't something
I introduced.

**Next steps:**
Writing `tests/unit/test_health.py` (sub-task 4), modeled on
`test_review_service.py`'s `AsyncMock` fixture pattern. Then running
the full `make check` and `make test-unit` suite to document the
pre-existing failure baseline before opening the PR.

**Blockers:**
None currently — the Redis check in the same function has a separate,
known bug (#155) that always fails, so my test needs to account for
`health_check()` always raising `HTTPException` regardless of my fix.
Not a blocker, just something to design the test around.