## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Selection reasoning:**

I selected this Tier 1 issue because I am still becoming familiar with the PathReview codebase and wanted a focused first contribution. The issue has a clear scope limited to the health-check route and application settings, so it is a good fit for my current skill level while still giving me practice tracing configuration values through the backend.

**Problem summary:**

When we call the `GET /health` endpoint, the application crashes with an `AttributeError`. This happens because `api/routes/health.py` tries to check Redis status using `settings.redis_host`. However, the `Settings` model in `core/config.py` does not define this field, so it cannot find the host information. A successful fix will add `redis_host` to the configuration so the health check can report the Redis status correctly without any errors.

**Branch name:** fix/155-health-check-redis-settings

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Masaki0827/pathreview/commit/bd2afd230f27a299f980221308653af187130f20

**Reproduction summary:**

I reproduced the issue by starting the local services and calling `GET /health`.
The endpoint returned HTTP 503 and reported Redis as unhealthy even though the
Redis Docker container was healthy. The Redis health check failed because
`api/routes/health.py` accesses `settings.redis_host`, but the `Settings` model
in `core/config.py` defines only `redis_url`.

**PLAN.md link:** https://github.com/Masaki0827/pathreview/blob/fix/155-health-check-redis-settings/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

The health check expects separate `redis_host` and `redis_port` values, while
the existing configuration provides a single `redis_url`. I need to confirm
whether the preferred fix is to reuse `redis_url` directly or introduce
separate typed settings without creating duplicate configuration sources.
