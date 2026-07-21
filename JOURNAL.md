

## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/155#issuecomment-5026907677)

**Issue title:** Health check references settings.redis_host, which does not exist on Settings


**Tier:** [x] Tier 1 

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` builds its Redis client from
`settings.redis_host` and `settings.redis_port`, but the `Settings` class in
`core/config.py` never defines those attributes — it only exposes a single
`redis_url`. Because those fields don't exist, the Redis check raises an
`AttributeError` the moment it runs. That error gets swallowed by the endpoint's
broad `except Exception`, so instead of surfacing a clear configuration bug, the
check quietly marks Redis as `unhealthy` and the whole endpoint returns a 503 —
even when Redis itself is perfectly fine. The bug lives in the API health-check
route and its config source; a successful fix has the check read the field that
actually exists (`redis_url`) so the endpoint reports Redis's true status.

**Branch name:** docs/CONTRIBUTING.md

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger