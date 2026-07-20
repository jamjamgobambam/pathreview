# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The database portion of the application’s health check runs a simple `SELECT 1` query to confirm that PostgreSQL is reachable. However, the query is currently passed to SQLAlchemy as a plain string, which is not accepted by SQLAlchemy 2.x for textual SQL statements. This causes the health check to report that the database is unavailable even when the database itself is running normally. A successful fix will execute the probe using SQLAlchemy’s supported textual SQL format so that the health endpoint accurately reports database availability.

**Selection notes and scope reasoning:**
I selected this issue because it is labeled Tier 1 and provides a manageable first contribution to a large multi-service codebase while still involving real backend application logic. The issue has a clear failure condition, a specific affected route, and an expected outcome that can be reproduced and tested. The likely scope is limited to the health-check implementation and its related tests, so I can investigate it without needing to redesign unrelated modules. This makes the issue challenging enough to strengthen my understanding of FastAPI and SQLAlchemy while remaining realistic to complete within the module timeline.

**Branch name:** `fix/154-health-check-sqlalchemy-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
