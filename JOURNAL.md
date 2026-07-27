

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



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/PlacidoG/pathreview/commit/d942fa6

**Classification:** Bug (code defect). Not a feature gap — the Redis health check is
fully implemented and meant to work; it just reads config fields that don't exist. 
Not a docs issue — the source references undefined attributes.

**Reproduction summary:**
With Redis running and reachable (`redis-cli ping` → `PONG`), `GET /health` still returns
HTTP 503 and reports `redis: "unhealthy"`. The backend log shows
`redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"` —
`api/routes/health.py:45-46` reads `settings.redis_host`/`settings.redis_port`, but
`core/config.py` `Settings` defines only `redis_url`, so the `AttributeError` is thrown
(and swallowed by the broad `except Exception`) before Redis is ever pinged. A false
negative: Redis is healthy, the code just can't read its own config.

**Reproduction steps:**
1. `docker compose up -d` and confirm Redis is up: `docker exec pathreview-db-1 ... ` /
   `docker exec pathreview-redis-1 redis-cli ping` → `PONG`.
2. `alembic upgrade head` then `python scripts/seed_db.py`.
3. `uvicorn api.main:app --port 8000`.
4. `curl -i http://127.0.0.1:8000/health` → **HTTP 503**, body includes
   `"redis":"unhealthy"` (Postgres also flags via a separate `text("SELECT 1")` defect).
5. Backend log: `redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`.
6. Isolate the raise: `python -c "from core.config import settings; print(settings.redis_host)"`
   → `AttributeError`; contrast `settings.redis_url` → prints `redis://localhost:6379/0`.
7. **Automated proof:** `pytest tests/unit/test_health_check.py -v` → **FAILS** with
   `assert 'unhealthy' == 'healthy'` (Redis mocked as reachable, yet reported unhealthy).
   This red test lives at `tests/unit/test_health_check.py` and becomes the regression
   guard once the fix lands.

**Exact location:** root cause `api/routes/health.py:45` (`settings.redis_host`), with a
latent duplicate at `:46` (`settings.redis_port`). Fix will read `settings.redis_url`.

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]