# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` is supposed to report whether the app's Redis connection is healthy, but it tries to read `settings.redis_host` and `settings.redis_port` off the `Settings` model in `core/config.py`, and neither field actually exists there — only `redis_url` is defined. Because of this mismatch, calling `GET /health` throws an `AttributeError` before the Redis probe can even run, so the endpoint fails outright instead of just reporting Redis as unavailable. This turns a check meant to give visibility into service status into something that crashes the request, which defeats the purpose for any monitoring or uptime tooling relying on it. A successful fix would update the Redis probe in `api/routes/health.py` to use configuration that actually exists on `Settings` — either by deriving host/port from the existing `redis_url`, or by adding proper `redis_host`/`redis_port` fields to `core/config.py` — so the endpoint returns accurate Redis status instead of erroring out. Since `/health` currently has no test coverage, a solid fix should also add a basic test confirming the endpoint behaves correctly when Redis is reachable and when it isn't.

**Issue checklist reasoning:**
This is a small, well-scoped Tier 1 bug: the root cause is a one-line attribute mismatch between two files (`api/routes/health.py` and `core/config.py`), it's easy to reproduce (`GET /health`), and the fix doesn't require touching the frontend, database schema, or other modules. It's a good fit for a first contribution because the blast radius is contained to the health-check path and there's a clear, testable definition of "done" (endpoint returns 200 with real Redis status instead of erroring). One risk I noted: this issue is popular — several classmates have already claimed it and there are multiple linked PRs (#160, #177, #188, #208) attempting to close it — so there's a real chance it gets resolved by someone else before I finish. I'm proceeding anyway since I already claimed it and understand the fix, but I'm keeping my changes small and self-contained so I can pivot quickly if it closes out from under me.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
