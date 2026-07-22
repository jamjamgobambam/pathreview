## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** <br> [x] Tier 1  <br> [ ] Tier 2  <br> [ ] Tier 3

**Problem summary:**
The `/health` endpoint checks database connectivity by calling `db.execute()`
with a raw SQL string (`"SELECT 1"`). SQLAlchemy 2.x removed implicit string
execution. The raw SQL must be wrapped in `text()`, so this call throws an
exception on every request. As a result, the health check always reports
Postgres as unhealthy and returns a 503, even when the database is running
fine. This affects `api/routes/health.py`. The fix wraps the query in
`sqlalchemy.text()` so it executes correctly and the endpoint accurately
reflects database health.

**Selection notes (Is this right for me? checklist):**
I could explain the issue and expected fix without re-reading it, located
the exact file and line via:
```bash
grep -rn "@router" api/ --include="*.py" | grep -i health
```

and confirmed the fix scope was a single file/single line change. I verified via `curl` that Postgres now reports healthy after the fix; the endpoint still returns 503 overall due to an unrelated Redis config bug  (issue #155), which is out of scope for this PR.

**Branch name:** fix/154-health-check-raw-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger