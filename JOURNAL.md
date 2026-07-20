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


