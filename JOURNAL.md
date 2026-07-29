## Week 7 -- Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint in the API layer tries to connect to Redis using `settings.redis_host` and `settings.redis_port`, but those settings are not defined in the application's configuration. The current `Settings` class only exposes `redis_url`, so the endpoint can raise an attribute error or incorrectly report Redis as unhealthy. This makes the `/health` route unreliable for local development and deployment checks. A successful fix would make the health check use the real Redis configuration path and return accurate dependency status.

**Branch name:** fix/156-health-check-redis-settings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
This issue is a good fit for me because I can explain it clearly in my own words: the health check route is trying to use Redis settings that do not exist in the current configuration model, so the endpoint can fail even when Redis is configured correctly. The affected area is the API layer, and I located the relevant code in `api/routes/health.py` and the settings definition in `core/config.py`. I also understand what "done" looks like: after the fix, the health check should use the real Redis configuration path and report dependency status accurately instead of failing on missing attributes.

This matches Tier 1 because it is a localized bug fix in one small part of the codebase rather than a cross-system change. I have read the specific function involved and enough surrounding code to sketch a rough fix plan: update the Redis probe to use the existing `redis_url` setting and verify the endpoint behavior. The scope also looks realistic for Weeks 8-9 because it should stay within a small number of files and should mainly require a focused bug fix plus tests. Before implementation, I still need to confirm the exact test coverage for this module.

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** [224d77c](https://github.com/davidobi2911/pathreview/commit/224d77c)

**Reproduction summary:**
I reproduced the issue locally on Wednesday, July 29, 2026 by calling the health route with a healthy mocked database session through the project virtual environment. The route logged `'Settings' object has no attribute 'redis_host'`, marked Redis unhealthy, and raised `HTTPException 503`, which matches the config mismatch between `api/routes/health.py` and `core/config.py`.

**PLAN.md link:** [PLAN.md](https://github.com/davidobi2911/pathreview/blob/fix/156-health-check-redis-settings/PLAN.md)

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
The local notes disagree on the issue number: my existing Week 7 entry and branch name reference `#156`, but the issue text I am working from says `#155`. I also still need to choose whether the Week 9 fix should use `redis.from_url(...)` directly or parse `redis_url` before building the client.
