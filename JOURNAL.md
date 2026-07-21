# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` tries to build a Redis client using `settings.redis_host` and `settings.redis_port`, but the `Settings` class in `core/config.py` only defines a single `redis_url` field — those two attributes don't exist. Every call to the health check therefore raises an `AttributeError` while checking Redis, which gets silently caught by a broad `except Exception` and reported as `"redis": "unhealthy"`. This makes the endpoint useless for its actual purpose: it always reports Redis as down, even when Redis is running fine, and hides the real bug (a code error, not an infrastructure problem) from anyone reading the health status. A successful fix builds the Redis client from `settings.redis_url` directly (e.g. `redis.Redis.from_url(...)`) so the health check accurately reflects Redis's real status, plus a test that exercises `/health` so this kind of attribute-name drift is caught automatically next time.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Selection notes (fit checklist):**
- Scope: touches exactly one file (`api/routes/health.py`) plus a new/updated test — small, well-bounded for a first contribution.
- Comfort: Tier 1 (`good first issue`) label, and I verified the root cause myself by reading `core/config.py` alongside `health.py` before claiming — it's a straightforward attribute mismatch, not a design question.
- Risk: low — the fix doesn't change the health check's contract (still returns the same JSON shape / status codes), just makes the Redis check work correctly.
- Learning value: touches Pydantic Settings, the `redis-py` client API, and error-swallowing anti-patterns (`except Exception` masking bugs), which felt like a good first exposure to this codebase's conventions.
