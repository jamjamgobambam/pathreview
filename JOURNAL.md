## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check tries to connect using `settings.redis_host`
and `settings.redis_port`, but the `Settings` model only defines a single combined
`redis_url` field. This caused an `AttributeError` every time the Redis check ran,
so the health endpoint always reported Redis as "unhealthy" even when Redis was
working fine. I fixed it by using `redis.Redis.from_url(settings.redis_url)` instead,
which correctly parses the existing connection string. This affects the `api/routes/health.py`
file and required no changes to the `core/config.py` settings themselves.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger