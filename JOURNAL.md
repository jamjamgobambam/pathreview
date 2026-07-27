## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/155](https://github.com/ascherj/pathreview/issues/155)

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The Redis probe in `api/routes/health.py` reads `settings.redis_host`, but the `Settings` model in `core/config.py` does not define that field. As a result, a request to `GET /health` raises an `AttributeError` before the endpoint can report Redis health. A successful fix will make the health endpoint use configuration that actually exists and allow it to return Redis status without crashing.

**Branch name:** `fix/155-health-check-redis-config`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
