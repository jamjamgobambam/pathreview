## Week 7 -- Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint in the API layer tries to connect to Redis using `settings.redis_host` and `settings.redis_port`, but those settings are not defined in the application's configuration. The current `Settings` class only exposes `redis_url`, so the endpoint can raise an attribute error or incorrectly report Redis as unhealthy. This makes the `/health` route unreliable for local development and deployment checks. A successful fix would make the health check use the real Redis configuration path and return accurate dependency status.

**Branch name:** fix/156-health-check-redis-settings

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes:**
This issue looks small in scope and localized to the API health check code, so it is a good Tier 1 starting point. It does not require changing the database schema, frontend UI, or broad application behavior. The main work is understanding how configuration is loaded and updating the Redis probe to match the existing settings model.
