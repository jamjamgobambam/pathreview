## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint checks Redis by reading `settings.redis_host` and
`settings.redis_port`, but `Settings` in `core/config.py` never defines those
fields — it only has `redis_url`. So this line always throws an
`AttributeError`, which gets caught and just marks Redis as unhealthy, even
when Redis is actually running fine. That means the health check can never
correctly report Redis status. A successful fix would update the Redis check
to use the connection info that actually exists in `Settings`, so the health
check reports Redis's real status instead of always failing.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
