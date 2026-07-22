## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/154#issuecomment-5039403002]

**Issue title:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that the database health check or probe within the ap/routes/health.py route is passing a raw SQL string plainly rather than explicitely marking the expression or string using sqlalchemy.text() so SQLAlchemy can correctly interact with the expression. Since SQLAlchemy doesn't expect a raw string, it raises an ArgumentError instead. As a result, the /health endpoint is incorrectly reported as unnavailable even though the connection is working properly or is reachable. A successful fix would wrap the string with the sqlalchemy.text() call within the api/routes/health.py file at the "SELECT 1" portion would allow the Get /health api endpoint call using curl to be successful and return the appropriate health records.

**Branch name:** [fix/154-DB-Probe-SQL-Input-Error]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger