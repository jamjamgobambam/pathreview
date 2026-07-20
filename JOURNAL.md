## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
SQLAlchemy 2.x won't execute raw SQL without wrapping it in `text()`, but the health check endpoint in `api/routes/health.py` doesn't do that. It just passes "SELECT 1" directly, which breaks the `/health` endpoint even when the database is fine. That defeats the whole point of a health check—you can't verify database connectivity. Wrapping the SQL string in `text()` restores that functionality so the endpoint actually confirms the database is up.

**Why this one:** My first open source contribution, so I wanted something contained to one file rather than a sprawling change.

**Branch name:** fix/154-health-check-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger