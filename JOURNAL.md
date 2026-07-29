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

**Setup confirmation:** [x] App runs locally at localhost:5173

*Note: on my machine, port 5173 was already occupied by an unrelated local project, so Vite
auto-selected 5174 instead (`http://localhost:5174`) — confirmed it's genuinely the PathReview
frontend (page `<title>PathReview - AI Portfolio Review Assistant</title>`), not a stale
process. Backend confirmed running at `http://localhost:8000` per SETUP.md (also shifted to
8010 locally for the same reason). This is a local port-conflict artifact, not a project bug.*

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction and planning

**Reproduced locally:** Yes. Ran `docker compose up -d`, `alembic upgrade head`, and
`uvicorn api.main:app`, then called `GET /health`. Confirmed the exact `AttributeError` from
the issue:

```
2026-07-29 00:45:07 [error] redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"
```

**Important nuance found during reproduction:** the `AttributeError` is caught by an existing
`except Exception` block in `api/routes/health.py`, so the endpoint doesn't crash outright —
it silently reports `"redis": "unhealthy"` no matter what Redis's real status is. Full details
and my fix approach are in [PLAN.md](PLAN.md).

**Plan:** See [PLAN.md](PLAN.md) — root cause, files to change, step-by-step plan, test
specification, and risks/edge cases.

**Loom walkthrough:** [ ] Recorded (not yet — recommended but not graded)
