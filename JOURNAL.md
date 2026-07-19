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