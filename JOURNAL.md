# JOURNAL.md

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The database portion of the application's health check runs a simple `SELECT 1` query to verify that PostgreSQL is reachable. However, the query is currently passed to SQLAlchemy as a plain string, which is not supported in SQLAlchemy 2.x for textual SQL statements. As a result, the health check can incorrectly report that the database is unavailable even when it is running normally. A successful fix will update the query to use SQLAlchemy's supported syntax so the health endpoint accurately reports the database status.

**Why I selected this issue:**

I chose this issue because it seemed like a good balance between being challenging and manageable. It focuses on a real backend bug instead of a simple documentation change, so I can learn more about SQLAlchemy and how the application's health check works. Since it is a Tier 1 issue with a clear scope, I felt it was a good first contribution to a larger open-source codebase.

**Branch name:** `fix/154-health-check-sqlalchemy-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** *(Will be added after creating the reproduction commit.)*

**Reproduction summary:**

I reproduced the issue by starting the PathReview application and confirming that the PostgreSQL Docker container was healthy. I then requested the `GET /health` endpoint using `curl`, and the endpoint returned HTTP 503 while reporting PostgreSQL as unhealthy even though the database container itself was running normally. I traced the behavior to `api/routes/health.py`, where the health check executes `SELECT 1` as a plain SQL string.

**PLAN.md link:** *(Will be added after creating PLAN.md.)*

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**

I still need to confirm the exact SQLAlchemy 2.x syntax required for executing textual SQL and determine whether any existing tests need to be updated or if a new test should be added.