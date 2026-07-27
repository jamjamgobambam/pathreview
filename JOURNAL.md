## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The `/health` endpoint includes a database probe that checks whether the application's database is reachable. Currently, it executes the SQL query `"SELECT 1"` as a plain string, which is incompatible with SQLAlchemy 2.x and causes the database check to raise an error instead of succeeding. As a result, the health endpoint incorrectly reports that the database is unavailable even when it is reachable. A successful fix will update the query to use SQLAlchemy's `text()` wrapper so the database probe executes correctly and the health endpoint accurately reflects the application's status.

**Branch name:** `fix/154-health-check-db-probe`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue selection notes ("Is this right for me?")

I selected this Tier 1 issue because it has a clearly defined scope and affects a single part of the API layer. The issue description identifies the relevant file (`api/routes/health.py`), making it straightforward to locate the code and understand the expected behavior before and after the fix. Since this is my first contribution to a larger codebase, I wanted a well-scoped issue that I can confidently reproduce, test, and complete within the project timeline.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [will update after commit]

**Reproduction summary:**

I reproduced issue #154 by running the application locally and sending a request to the `/health` endpoint using curl. The endpoint returned a 503 response and the PostgreSQL dependency was marked as unhealthy because SQLAlchemy 2.x rejected the raw SQL query `"SELECT 1"` with an error requiring it to be wrapped using `text()`.

**PLAN.md link:** [will update after creating PLAN.md]

**Walkthrough video (recommended):** Not recorded (optional)

**Blockers or open questions:**

The Redis health check also reports a separate configuration error, but it appears unrelated to issue #154 and is outside the scope of this contribution.