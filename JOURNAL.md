## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/154)

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x
 #154

**Tier:** [yes] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The database health check in api/routes/health.py executes "SELECT 1" as a plain Python string. Under SQLAlchemy 2.x, textual SQL statements must be explicitly wrapped with sqlalchemy.text(), so the current database probe raises an ArgumentError. Because the exception is caught by the health-check logic, the application incorrectly reports the database as unavailable even when PostgreSQL is running normally. A successful fix will wrap the query correctly, allow the probe to execute, and ensure the /health endpoint reports the actual database status.

**Branch name:** fix/154-db-argument-error

**Setup confirmation:** [yes] App runs locally at localhost:5173

**Cohort ledger:** [yes] Issue added to cohort ledger


**Setup notes**

I forked the PathReview repository, cloned my fork, and added the original repository as the upstream remote. I created and pushed the working branch fix/154-db-argument-error.

I successfully ran make setup, which installed the Python and frontend dependencies, applied the database migrations, and seeded the development database. I then ran make run and confirmed that the frontend loaded at http://localhost:5173, the API started at http://localhost:8000, and I could log in using the provided test account user1@example.com.

The setup displayed a bcrypt version compatibility warning, but authentication and the rest of the application continued to work. Because that warning is unrelated to issue #154, I will not modify the authentication dependencies as part of this contribution.



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/japhet125/pathreview/commit/35cbe6d1a2e091a6769373d5e2de6ac44ec4ddef)

**Reproduction summary:**
I started the PostgreSQL and Redis services with Docker Compose and confirmed that both containers were healthy. I then called GET http://localhost:8000/health, which returned 503 Service Unavailable and reported PostgreSQL as "unhealthy". The PostgreSQL probe in api/routes/health.py calls await db.execute("SELECT 1") at line 31, causing SQLAlchemy 2.x to reject the raw textual SQL statement even though the PostgreSQL container is reachable.


**PLAN.md link:** (https://github.com/japhet125/pathreview/blob/fix/154-db-argument-error/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
The /health response also reported Redis as unhealthy even though the Redis container was healthy and responded to redis-cli ping with PONG. This appears to be a separate configuration or connectivity issue and is outside the scope of issue #154. I will ensure that my code change is limited to the PostgreSQL probe and does not modify Redis configuration.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I reproduced issue #154 locally and confirmed that the PostgreSQL health probe failed because SQLAlchemy 2.x does not allow raw textual SQL statements to be passed directly to `db.execute()`. I identified the root cause in `api/routes/health.py` and updated the query to use `sqlalchemy.text("SELECT 1")`. After updating the query to await db.execute(text("SELECT 1")) and restarting the application, the /health endpoint correctly reported PostgreSQL as "healthy" instead of "unhealthy", confirming that the SQLAlchemy 2.x compatibility issue was resolved.

**Next steps:**

* Review the final implementation.
* Update the project documentation.
* Open a pull request.
* Request peer or mentor feedback.
* Address any review comments before marking the PR ready for review.

**Blockers:**

The repository contains several pre-existing linting and type-checking issues across multiple files that are unrelated to issue #154. My implementation only modifies the PostgreSQL health probe and does not introduce any additional linting or type-checking failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/582

**Branch:** `fix/154-db-argument-error`

**What you built:**

This change fixes the PostgreSQL health probe so it works correctly with SQLAlchemy 2.x. The health check now wraps the textual SQL query with `sqlalchemy.text()`, allowing the database probe to execute successfully instead of raising an `ArgumentError`. After the fix, PostgreSQL is correctly reported as `"healthy"` when reachable.

**Tests added or updated:**

No new automated tests were added because this fix only changes the SQLAlchemy 2.x syntax used by the PostgreSQL health probe. The fix was verified manually by reproducing the issue before the change and confirming that the /health endpoint reported PostgreSQL as "healthy" after wrapping the query with sqlalchemy.text(). Existing Redis failures were confirmed to be unrelated to this issue.

**Self-review confirmation:**

* [ ] make check passes
* [ ] make test-unit passes
make check and make test-unit report pre-existing repository issues unrelated to issue #154. My changes did not introduce any new failures.

The project contains pre-existing linting and typing issues unrelated to this change. My modification did not introduce any additional failures.
make test-unit reports existing failures unrelated to issue #154. This PR only changes the PostgreSQL health probe and does not introduce additional test failures.

**Draft PR feedback received from:**

None
