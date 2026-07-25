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