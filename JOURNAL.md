## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The app's health check endpoint verifies the database is reachable by running a small probe query, but it passes that query to SQLAlchemy as a plain Python string instead of wrapping it in SQLAlchemy's `text()` construct. SQLAlchemy 2.x removed the automatic coercion that used to let raw strings work as executable SQL, so the probe now throws an error instead of returning a healthy status. This means the health check endpoint — which other services or monitoring tools may rely on to confirm the API is up — can report false failures even when the database is actually fine. A successful fix updates the DB probe to use the correct SQLAlchemy 2.x-compatible syntax so the health check accurately reflects database connectivity again. This affects the API layer, specifically the health check route and its database session handling.

**Branch name:** fix/154-health-check-raw-sql-string

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger