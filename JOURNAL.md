## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` checks Postgres connectivity by calling
`db.execute("SELECT 1")` with a plain Python string. SQLAlchemy 2.x no longer accepts raw
strings for textual SQL — they must be wrapped in `sqlalchemy.text()` — so the call raises
an `ArgumentError` instead of running the query. Because that exception is caught by the
surrounding `try/except`, the health check reports Postgres (and the overall service) as
unhealthy even when the database is up and reachable. A correct fix wraps the query string
in `text("SELECT 1")` so the probe actually executes and reflects the real DB status.

**Branch name:** fix/154-health-check-textual-sql

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
