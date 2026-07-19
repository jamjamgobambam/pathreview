## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The database health check in `api/routes/health.py` runs a raw SQL string
("SELECT 1") directly against the database connection. SQLAlchemy 2.x
requires literal SQL to be explicitly wrapped in `sqlalchemy.text()` before
execution — passing a bare string now raises an `ArgumentError` instead of
running the query. As a result, the `/health` endpoint reports the database
as down even when it's fully reachable, which is misleading for anyone
(or any monitoring tool) relying on that endpoint to reflect real system
status. A successful fix wraps the query in `text()` so the probe executes
correctly and the health check accurately reflects the database's actual
state.

**Branch name:** fix/154-health-check-sqlalchemy-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger