## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [ X ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint (`api/routes/health.py`) checks Redis by building a client
with `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`. But the
`Settings` class in `core/config.py` never defines `redis_host` or `redis_port` — it
exposes a single `redis_url` instead. So the attribute lookup raises
`AttributeError: 'Settings' object has no attribute 'redis_host'` before a connection
is ever attempted. The surrounding `try/except` swallows that error, marks Redis
`"unhealthy"`, and the endpoint returns 503 regardless of whether Redis is actually
up — which defeats the point of a health check. A successful fix rebuilds the client
from the attribute that actually exists (`redis.Redis.from_url(settings.redis_url,
...)`), so `/health` reports Redis's real state instead of failing on a bad config
reference.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?" checklist reasoning

- **Scope is bounded and understood.** The bug lives in one function in one file
  (`api/routes/health.py`). I traced it end to end with the VS Code debugger: sent a
  `GET /health`, hit a breakpoint in the Redis block, and read the caught exception
  in Locals — `AttributeError("'Settings' object has no attribute 'redis_host'")`.
  I can explain both the cause (attribute doesn't exist) and the effect (`except`
  swallows it, so the endpoint always returns 503).
- **The fix is small and low-risk.** Replace the `host=/port=` construction with
  `redis.Redis.from_url(settings.redis_url, ...)`, matching the attribute the
  `Settings` class already exposes. No schema, migration, or API-contract change.
- **I can verify it.** I have the backend running locally and a saved request that
  reproduces the 503, so I can confirm the Redis dependency flips to `"healthy"`
  (with Redis up) once the fix lands.
- **Out of scope, deliberately.** While reproducing this I noticed `/health` also
  reports Postgres unhealthy — but for a different reason (`db.execute("SELECT 1")`
  needs SQLAlchemy's `text()` wrapper). That is not issue #155. I'm leaving it
  untouched to keep this branch to one intent; it belongs in its own issue/PR.