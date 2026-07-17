## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings #155

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:** The problem is that the health check endpoint in 'api/routes/health.py' tries to read a 'redis_host' attribute from the app's 'Settings' object to run its Redis probe, but this field does not exist in 'Settings.' Because of this, the endpoint breaks entirely due to the 'AttributeError'. A fix to this problem would be to update the health check to reference the right Settings field or add a field if it is missing, so '/health' will be able to report Redisok status without the endpoint breaking.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
