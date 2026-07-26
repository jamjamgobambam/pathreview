## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Branch name:** `fix/155-health-check-redis-settings`

**Problem summary:**
The `/health` endpoint checks PostgreSQL, Redis, and vector DB status, but its Redis check originally read `settings.redis_host` and `settings.redis_port` even though the app's `Settings` model only defines `redis_url`. Because of that mismatch, the Redis check could not use the configured Redis connection information correctly and would mark Redis as unhealthy, contributing to a 503 response.

**Why I chose this issue:**
I chose this issue because it is a clearly scoped Tier 1 backend bug and it touches service health/configuration, which I find interesting. It also seemed like a good fit for a first contribution because the affected area was narrow and the bug could be traced to a specific mismatch between the route code and the settings model.

**Affected area:**
- `api/routes/health.py`
- `core/config.py`

**Confirmed investigation notes:**
- `health.py` originally used `settings.redis_host` and `settings.redis_port`
- `core/config.py` defines `redis_url`, but not `redis_host` or `redis_port`
- The Redis exception is caught inside the route, so the issue is not an uncaught crash
- Instead, Redis is marked unhealthy and the route can return HTTP 503

**Known unknowns during investigation:**
- Whether the smallest clean fix should parse the URL manually or use a Redis URL-based constructor
- Whether there was already an existing health-route test pattern in the repo
- Whether Docker would be required for all validation or whether mocked unit tests would be enough for this issue

**Scope estimate:**
Small Tier 1 backend fix, likely 1 source file plus 1 focused test file.

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue claim:** [x] Comment posted on GitHub issue

**Setup progress:**
- [x] Forked repo
- [x] Cloned repo
- [x] Created virtual environment
- [x] Installed Python dependencies with editable install
- [x] Repaired WSL/Docker startup issue on Windows
- [ ] App fully runs locally at `localhost:5173`

**Docker / environment blocker:**
Docker image pulls for local services were blocked by repeated EOF errors while downloading:
- `postgres:16-alpine`
- `redis:7-alpine`
- `chromadb/chroma:0.4.22`

Because of that, I could not fully bring up the repo's Docker-backed services locally. However, I was still able to continue issue investigation and write focused mocked unit tests for this issue.

**Testing investigation:**
There were no existing FastAPI `TestClient` tests or health-route tests in the repo. The best nearby patterns were:
- `tests/unit/test_review_service.py` for `AsyncMock` database usage
- `tests/unit/test_rate_limiter.py` for Redis mocking

Based on that, I created:
- `tests/unit/test_health.py`

**Tests added:**
1. `test_health_check_returns_healthy_when_dependencies_are_healthy`
2. `test_health_check_uses_redis_url_from_settings`

These tests call `health_check()` directly with mocked dependencies instead of relying on Docker services.

**Implementation progress:**
I updated the Redis health check in `api/routes/health.py` to use the existing `settings.redis_url` configuration rather than missing `redis_host` / `redis_port` settings.

**Validation status:**
Focused issue tests now pass locally:

```powershell
.\.venv\Scripts\python -m pytest tests/unit/test_health.py -v
.\.venv\Scripts\python -m pytest tests/unit/test_health.py tests/unit/test_rate_limiter.py -v
```

Result:

* 21 passed

**Current status:**
Issue claimed and added to ledger, working branch created and pushed, journal updated, focused fix implemented, PR opened, and focused validation completed with 21 passing unit tests.

## Week 8 — Reproduction and planning

**Reproduced issue:**
I reproduced the issue by tracing the Redis health check in `api/routes/health.py` and confirming it used `settings.redis_host` and `settings.redis_port`, while `core/config.py` only defines `redis_url`. Before the fix, focused tests failed because Redis was marked unhealthy and the route returned HTTP 503.

**Observed behavior:**
Before the fix, the Redis health check raised an internally caught `AttributeError` because `Settings` had no `redis_host` attribute. The route then marked Redis as unhealthy and raised HTTP 503.

**Expected behavior:**
The health route should use the application's existing Redis configuration source, `settings.redis_url`. When Redis responds to `ping()`, the route should report Redis as healthy without requiring duplicate `redis_host` or `redis_port` settings.

**Plan summary:**
My plan was to keep the fix minimal by using the existing `settings.redis_url` configuration instead of introducing new settings fields. Since Docker-backed services were blocked by image pull EOF errors, I used mocked unit tests to validate the health route behavior without relying on live Postgres, Redis, or Chroma containers.

**Approach:**

1. Add focused tests in `tests/unit/test_health.py`
2. Mock database and Redis behavior directly
3. Update the Redis health check to use `settings.redis_url`
4. Re-run focused tests and nearby Redis-related unit tests

**Relevant files:**

* `api/routes/health.py`
* `core/config.py`
* `tests/unit/test_health.py`
* `tests/unit/test_review_service.py`
* `tests/unit/test_rate_limiter.py`

**Known unknowns resolved:**

* I confirmed there were no existing FastAPI `TestClient` tests or health-route tests.
* I confirmed direct async testing of `health_check()` with mocks was enough for focused unit validation.
* I confirmed `redis_url` was the existing source of truth for Redis configuration.
* I confirmed Docker was not required for the focused mocked unit tests.

**Validation for plan/fix:**

* `tests/unit/test_health.py` passed
* `tests/unit/test_health.py` and `tests/unit/test_rate_limiter.py` passed
* Total: 21 passing tests

**Blockers:**
Docker image pulls for local services were blocked by repeated EOF errors, so full Docker-backed runtime verification was not possible on my machine.

**Week 8 current status:**
`PLAN.md` has been created, the issue has been reproduced, the solution plan is documented, the focused fix is implemented, the PR is open, and relevant mocked unit tests are passing.