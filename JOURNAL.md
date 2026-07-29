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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/adhik-adhikari/pathreview/commit/7350da83f0b5b633387f34392da9785790d6f287

**Reproduction summary:**
I ran the app locally against the Dockerized Postgres/Redis/Chroma services and called `GET /health` directly, which returned a 503 with `"redis": "unhealthy"` and logged `'Settings' object has no attribute 'redis_host'` — matching the issue exactly, even though the Redis container was healthy the whole time. I also added a failing integration test (`tests/integration/test_health.py`) and a unit test (`tests/unit/test_health_check.py`) that reproduce the bug and will guide the fix in Week 9.

**PLAN.md link:** https://github.com/adhik-adhikari/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Still need to confirm whether other modules that accept an injected `redis_client` (`agent/memory/session_store.py`, `safety/rate_limiter.py`, `safety/monitoring.py`) expect the client to be constructed the same way I plan to fix the health check (`redis.Redis.from_url(settings.redis_url)`), so the fix stays consistent with the rest of the app.
