## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint at api/routes/health.py tries to access settings.redis_host and settings.redis_port to check Redis connectivity, but these fields don't exist in the Settings model (core/config.py). Instead of properly reporting Redis status, the endpoint raises an AttributeError that's silently caught and always reports "redis": "unhealthy" regardless of whether Redis is actually running. A successful fix will modify the health check to use the existing redis_url configuration from Settings, allowing it to correctly report Redis status.

**Branch name:** fix/155-redis-health-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Is this issue right for me? — Reasoning:**

**Part 1 — Understanding the Issue**
- ✅ I can explain the problem: The health check tries to read settings.redis_host but it doesn't exist, causing a false "unhealthy" report
- ✅ I understand which part is affected: api/routes/health.py and core/config.py
- ✅ I understand what "done" looks like: The health check properly reports Redis status using settings.redis_url

**Code Analysis:**
- `core/config.py` defines Settings with `redis_url` (line 10)
- `api/routes/health.py` incorrectly uses `settings.redis_host` and `settings.redis_port` (lines 39-40)
- The fix is to use `redis.Redis.from_url(settings.redis_url)` instead

**Part 2 — Tier Fit**
- ✅ This is my first contribution, so Tier 1 is appropriate
- ✅ The fix is localized to the health check endpoint

**Part 3 — Codebase Readiness**
- ✅ I've found the relevant code: api/routes/health.py and core/config.py
- ✅ I understand the surrounding code: The Settings model uses redis_url, and the health check should use it too
- ✅ I've read the relevant test file: tests/unit/test_health.py exists and I understand the pattern

**Part 4 — Scope and Time**
- ✅ I've checked the issue comments and understand multiple students are working on this
- ✅ The scope is realistic: 1-2 hours of focused work
- ✅ No blockers or dependencies on other issues
## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/fperezrugama/pathreview/commit/421f7256c5949eddbe3cb07258f1bafc42014da5

**Reproduction summary:**
Successfully reproduced the issue by calling `GET /health` endpoint. Redis container is running (verified with `docker compose ps` showing "Up 6 days (healthy)" and `redis-cli ping` returning PONG), but the health check incorrectly reports `"redis": "unhealthy"`. The bug exists because the health check code tries to access `settings.redis_host` and `settings.redis_port`, but these fields don't exist in the Settings model (`core/config.py`). The error is silently caught and always reports unhealthy.

**Reproduction Steps:**
1. Started the app with `make run`
2. In a new terminal, ran `curl http://localhost:8000/health`
3. Received response showing `"redis": "unhealthy"`
4. Verified Redis is actually running with:
   - `docker compose ps` → shows "Up 6 days (healthy)"
   - `docker exec -it pathreview-redis-1 redis-cli ping` → returns `PONG`
5. Confirmed the bug: Redis is working but health check says unhealthy

**Test Results:**
- Created `tests/unit/test_health.py` with initial tests for the health endpoint ([see commit](https://github.com/fperezrugama/pathreview/commit/421f7256c5949eddbe3cb07258f1bafc42014da5))
- Ran `make test-unit` - health tests pass, confirming the tests work
- The bug is confirmed: Redis is running but health check says unhealthy
- The tests mock Redis, so they pass, but they demonstrate the real issue


