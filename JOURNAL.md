# Development Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** ☑ Tier 1  ☐ Tier 2  ☐ Tier 3

**Problem summary:**

The health check endpoint attempts to create a Redis client using `settings.redis_host` and `settings.redis_port`, but these configuration values do not exist in `core/config.py`. As a result, the endpoint raises an `AttributeError` instead of completing the health check. A successful fix updates the health check to use the existing `settings.redis_url` configuration so the endpoint can initialize the Redis client correctly.

**Branch name:** `fix-health-check-redis-host`

**Setup confirmation:** ☑ App runs locally at `localhost:5173`

**Cohort ledger:** ☑ Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
(To be added after committing)

**Reproduction summary:**
I reproduced the issue by running the application locally and sending a request to the `/health` endpoint. The health check attempted to access `settings.redis_host` and `settings.redis_port`, which do not exist in the application's configuration, causing the endpoint to fail. I verified that the application already uses `settings.redis_url`, making it the correct configuration to use.

**PLAN.md link:**
(To be added after pushing)

**Walkthrough video (recommended):**
N/A

**Blockers or open questions:**
The repository has existing lint and type-check issues in `api/routes/health.py` that are unrelated to this issue and prevented the pre-commit hooks from passing locally.