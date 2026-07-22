## Week 7 — Issue selection

**Issue link:** [#155](https://github.com/ascherj/pathreview/issues/155)

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report the status of Postgres, Redis, and the
vector DB, but its Redis probe reads `settings.redis_host` and `settings.redis_port` in
`api/routes/health.py`, and neither field is defined on the `Settings` model in
`core/config.py` — only a single `redis_url` field exists. This raises an `AttributeError`
on every call, which is swallowed by the surrounding `try/except`, so Redis is always
reported `unhealthy` and the endpoint returns a 503 even when Redis is actually up. A
successful fix updates the probe to build the Redis client from `settings.redis_url` so
the health check accurately reflects Redis's real status.

**Branch name:** `fix/155-redis-health-check`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger