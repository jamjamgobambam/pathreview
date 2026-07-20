## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint's database probe, in `api/routes/health.py`, runs the raw SQL string `"SELECT 1"` directly against the database session. SQLAlchemy 2.x no longer accepts bare strings for textual SQL — it requires them to be wrapped in `sqlalchemy.text()` — so the probe throws an `ArgumentError` and the `/health` endpoint reports the database as unreachable even when it's working fine. A successful fix wraps the query string in `text()` so the probe executes correctly and the health check accurately reflects the database's real status.

**Branch name:** fix/154-health-check-sql-text-wrap

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger