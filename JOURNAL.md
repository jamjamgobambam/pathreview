## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint in api/routes/health.py tries to read a setting
called redis_host to check if Redis is working. This setting does not exist
on the Settings model. Only redis_url exists there. Because of this, calling
GET /health crashes with an AttributeError before it can report Redis status.
A correct fix will build the Redis connection from redis_url instead, so the
health check can run without crashing and give a clear status for Redis.

**Checklist notes:**
This issue is Tier 1, and the fix is contained to one file, api/routes/health.py. I confirmed the bug directly, redis_host is used in that file but does not exist in Settings, only redis_url does. The codebase and test setup is not fully explored yet, that will happen in Week 8. Many students have claimed this issue and one PR is already open, but claims are non-exclusive, so I am comfortable with the overlap. The scope looks realistic for the Weeks 8-9 timeline. Once I am more comfortable with the codebase, I may take on a second issue at a higher tier as a stretch goal.

**Branch name:** fix/155-redis-host-config

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger