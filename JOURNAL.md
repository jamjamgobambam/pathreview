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
