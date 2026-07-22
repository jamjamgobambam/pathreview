## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint in `api/routes/health.py` is supposed to check whether the PostgreSQL database is reachable by running a simple `SELECT 1` query. However, the query is passed as a plain Python string directly to SQLAlchemy's `execute()` method. SQLAlchemy 2.x no longer accepts raw strings as SQL — it requires them to be wrapped with `sqlalchemy.text()`. As a result, the probe raises an `ArgumentError` which is caught silently, causing the health check to always report postgres as "unhealthy" even when the database is fully operational. The fix is to import `text` from `sqlalchemy` and wrap the query: `await db.execute(text("SELECT 1"))`.

**Branch name:** fix/154-health-check-sqlalchemy-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
