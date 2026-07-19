# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint is meant to report whether PostgreSQL, Redis, and the
vector DB are reachable. To probe Redis, `api/routes/health.py` reads
`settings.redis_host` and `settings.redis_port`, but the `Settings` class in
`core/config.py` never defines those fields — it only defines `redis_url`.
Because of that mismatch, accessing `settings.redis_host` raises an
`AttributeError`, which the surrounding `try/except` catches and reports Redis as
"unhealthy," forcing the endpoint to return a 503 even when Redis is actually
running. A successful fix makes the health check read Redis connection details
that actually exist on `Settings` — e.g. deriving the host/port from `redis_url`
(or adding the missing fields) — so the endpoint reports Redis's true status.
This lives in the API layer's health/monitoring code (`api/routes/health.py` and
`core/config.py`).

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Selection notes — "Is this right for me?" reasoning

- **Do I understand the problem?** Yes. I traced it in the code: `health.py`
  references `settings.redis_host`/`settings.redis_port`, and `core/config.py`
  only defines `redis_url`, so the attribute access fails.
- **Is the scope bounded?** Yes — a Tier-1 bug touching just two files
  (`api/routes/health.py`, `core/config.py`), with no cross-module or frontend
  changes required.
- **Can I reproduce it?** Yes, per the issue: calling `GET /health` triggers the
  `AttributeError` path (caught and surfaced as Redis "unhealthy" → 503).
- **Do I have the skills?** Yes — it's straightforward Python / pydantic
  settings and a FastAPI route, no new frameworks to learn.
- **Can I verify the fix?** Yes — I can hit `GET /health` locally and confirm
  Redis reports its real status, and add/adjust a unit test for the health route.
- **Scope risk:** Low. The main decision is *how* to fix it (parse `redis_url`
  vs. add `redis_host`/`redis_port` fields); I'll confirm the preferred approach
  before implementing in Week 8.
