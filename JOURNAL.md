## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`health.py` passes a simple query to the database to check it is working. The query must be sent through a specific method, but the execute call receives it as a plain string, which raises an error. As a result, the health endpoint cannot tell whether the database is actually working. Wrapping the query in the required method would let the endpoint report the real database status.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" reasoning:**
This is my first open source contribution. So, I have chosen Tier 1. The issue 154 publisher has already described the cause of the problem and the affected file explicitly. I fully understood what is wrong with the endpoint. This fix is isolated to a single file, so the scope is small enough for me to handle.