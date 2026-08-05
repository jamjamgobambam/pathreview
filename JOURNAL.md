## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155
**Issue title:** Health check references settings.redis_host, which does not exist on Settings
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint at `/health` attempts to verify Redis connectivity by accessing `settings.redis_host` and `settings.redis_port`. However, the `Settings` model in `core/config.py` only defines a unified `redis_url` string, causing any request to `/health` to fail with an `AttributeError` before the status check can execute. Fixing this requires updating the health route probe in `api/routes/health.py` to connect via `redis.from_url(settings.redis_url)`. A successful fix will allow the health check to accurately report Redis status and return a `200 OK` response.

**Selection reasoning ("Is this right for me?"):**
This issue is isolated to a single route file (`api/routes/health.py`) and does not require modifying core business logic or complex data pipelines. It provides an immediate, tangible fix that restores API monitoring functionality while serving as a ideal starter issue to validate the full local environment and PR workflow.

**Branch name:** fix/155-health-redis-settings
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ssolvin/pathreview/commit/e41f34b6033cc4ecaa81252513860877d89c0480

**Reproduction summary:**
Executed `curl http://localhost:8000/health` against the local application. Observed that the Redis health probe fails and reports `"redis": "unhealthy"` because `api/routes/health.py` attempts to access non-existent `settings.redis_host` attribute on `Settings`, raising an internal `AttributeError`.
**PLAN.md link:** https://github.com/ssolvin/pathreview/blob/fix/155-health-redis-settings/PLAN.md

**Blockers or open questions:** None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Refactored `api/routes/health.py` to connect to Redis using `settings.redis_url` via `redis.Redis.from_url`.
- Written async unit test in `tests/unit/test_health.py` mocking `Redis.from_url`. Tested and verified passing with `pytest`.
- Pushed branch `fix/155-health-redis-settings` and created Draft PR #155 on upstream repository.

**Next steps:**
- Share Draft PR link in Slack cohort channel for peer/mentor review if time permits.
- Address any incoming review feedback.
- Run final `make check` and `make test-unit` sanity checks prior to marking ready for review.
- Complete Check-in 2 and submit branch URL before Sunday deadline.

**Blockers:**
- None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/973

**Branch:** `fix/155-health-redis-settings`

**What you built:**
Fixed an issue in `api/routes/health.py` where Redis health checks failed due to referencing missing `redis_host` and `redis_port` properties on `Settings`. Updated the endpoint to connect via `settings.redis_url` using `redis.Redis.from_url()`.

**Tests added or updated:**
`tests/unit/test_health.py`: added unit test patching `redis.Redis.from_url` to verify settings usage and health payload assertions.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** None