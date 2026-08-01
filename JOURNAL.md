# Week 7 — Issue selection

- **Issue link**: https://github.com/ascherj/pathreview/issues/155
- **Issue title**: Health check references settings.redis_host, which does not exist on Settings
- **Tier**: [x] Tier 1  [ ] Tier 2  [ ] Tier 3

## Problem summary:
The application's health check endpoint is failing because it attempts to access `settings.redis_host`, which is currently undefined in the `Settings` model within `core/config.py`. This causes an `AttributeError` when calling `GET /health`. I will resolve this by adding the missing `redis_host` field to the `Settings` configuration to allow the health check to function correctly.


## Selection Reasoning:
I selected this Tier 1 issue because it is a contained bug that allows me to get familiar with the project's configuration management without needing to refactor core business logic. It provides a clear, actionable path for my first contribution while helping me understand how the project handles settings.

- **Branch name**: fix/155-redis-host-settings
- **Setup confirmation**: [x] App runs locally at localhost:5173
- **Cohort ledger**: [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning
- **Reproduction commit link:** [\[reproduction commit \]](https://github.com/theoneineed/pathreview/commit/35e6f8c593ceed76407a20ca468a3c1dbbe20765)
- **Reproduction summary:**
I started the local server using `make run` and hit the backend API directly using `curl http://localhost:8000/health`. While the endpoint returned a JSON response, the application logs explicitly threw the error: `redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`, confirming the missing configuration field.
- **PLAN.md link:** https://github.com/theoneineed/pathreview/blob/fix/155-redis-host-settings/PLAN.md
- **Walkthrough video (recommended):** didn't make a video.
- **Blockers or open questions:** None.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
I successfully reproduced the bug and traced it to missing fields in `core/config.py`. I implemented the fix by adding `redis_host` and `redis_port` to the `Settings` class, matching the existing Pydantic `Field` patterns. Running the server locally confirms the `AttributeError` is gone and the Redis health check now passes.
**Next steps:**
I need to verify that `make check` and `make test-unit` have not introduced any new failures beyond the pre-existing baseline. After that, I will commit my changes, push to my branch, and open the Draft Pull Request.
**Blockers:**
None.


### Check-in 2 (end of week)
**PR link:** [I will add this link after opening the PR]
**Branch:** fix/155-redis-host-settings
**What you built:**
I fixed an `AttributeError` in the `/health` endpoint caused by missing Redis configuration fields. I updated the `Settings` class in `core/config.py` to include `redis_host` and `redis_port` with standard localhost defaults, matching the project's Pydantic `Field` patterns. This allows the health check to gracefully probe Redis without crashing the application.
**Tests added or updated:**
I created a new test file `tests/unit/test_config.py` because the configuration module previously lacked tests. I added `test_settings_redis_defaults` which verifies that the `Settings` model correctly initializes the new `redis_host` and `redis_port` fields with the expected default values.
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
**Draft PR feedback received from:** none