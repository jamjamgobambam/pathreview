# JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe should use SQLAlchemy text()

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The database portion of the application's health check runs a simple `SELECT 1` query to verify that PostgreSQL is available. Currently, the query is passed to SQLAlchemy as a plain string, which is not compatible with SQLAlchemy 2.x. This can cause the health endpoint to incorrectly report that the database is unhealthy even when it is running normally. A successful fix will execute the query using SQLAlchemy's supported `text()` function so the health check reports the database status correctly.

**Why I selected this issue:**

I chose this issue because it is a good introduction to working in a larger codebase while still requiring me to understand how SQLAlchemy works. It is more meaningful than a documentation-only task and will help me learn how backend health checks interact with the database. The scope is manageable for my current experience while still challenging enough to build new skills.

**Branch name:**

`fix/154-health-check-sqlalchemy-text`

**Setup confirmation:**

- [x] App runs locally at `http://localhost:5173`

**Cohort ledger:**

- [x] Issue added to cohort ledger

---

# Week 8 — Reproduction & solution planning

**Reproduction commit link:**

https://github.com/akodali65/pathreview/commit/1cc1317

**Reproduction summary:**

I reproduced the issue by running the PathReview application locally and checking the `/health` endpoint using `curl`. The endpoint returned PostgreSQL as unhealthy even though the PostgreSQL Docker container was running correctly. After tracing the code, I found that `api/routes/health.py` executes `SELECT 1` as a plain SQL string, which matches the issue description.

**PLAN.md link:**

https://github.com/akodali65/pathreview/blob/fix/154-health-check-sqlalchemy-text/PLAN.md

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

I want to verify whether changing the query to SQLAlchemy's `text()` function is the only modification required or whether any existing tests should also be updated to reflect the new behavior.