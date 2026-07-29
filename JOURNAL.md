# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report the status of the app's dependencies,
including Redis. To probe Redis, the handler in `api/routes/health.py` builds a client
from `settings.redis_host` and `settings.redis_port`. The problem is that the `Settings`
model in `core/config.py` never defines those fields — it only defines a single
`redis_url`. Because Pydantic settings don't expose attributes that weren't declared,
reading `settings.redis_host` raises an `AttributeError`, which crashes the Redis probe
before it can return anything. A successful fix makes `GET /health` complete without
error and report Redis as healthy/unhealthy — either by deriving host/port from the
existing `redis_url` (or adding the missing `redis_host`/`redis_port` fields) so the
handler and the config agree. This touches the API layer (`api/routes/health.py`) and
app configuration (`core/config.py`).

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope & fit reasoning

- **Tier fit:** This is a Tier 1 / "good first issue" labeled `bug` + `api`. As my first
  contribution to a large, unfamiliar multi-service codebase, Tier 1 matches my comfort
  level — I want to learn the contribution workflow (fork → branch → PR → review) without
  fighting a sprawling change at the same time.
- **Scope is small and bounded:** The bug is a concrete mismatch between two files
  (`api/routes/health.py` reads `settings.redis_host`/`redis_port`; `core/config.py`
  defines only `redis_url`). I confirmed this myself with `grep redis core/config.py`.
  The fix is a handful of lines in one or two files — no cross-cutting refactor.
- **I can reason about the root cause:** It's an `AttributeError` from referencing
  Pydantic settings fields that were never declared. I understand exactly why it happens
  and what "fixed" looks like.
- **Testable without the full stack:** The failure is at the config/handler boundary, so
  I can exercise it and verify the fix with a focused test rather than needing the entire
  Docker + Redis environment stood up.
- **Not too trivial to explain:** Unlike a pure typo, it requires deciding *how* the two
  should agree (derive host/port from `redis_url` vs. add explicit fields), which gives me
  something real to reason about and write up.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Rrahul0414/pathreview/commit/5f8666c26fd88868b79573ca986195534757149a

**Reproduction summary:**
I added `tests/unit/test_health.py` and ran it locally with pytest. With the DB and Redis
both stubbed as reachable, `GET /health` still returned **HTTP 503** with `redis: "unhealthy"`,
and the captured log showed `redis_health_check_failed error="'Settings' object has no
attribute 'redis_host'"` — confirming the handler reads a `Settings` field that doesn't
exist. A second test confirms `settings.redis_url` exists while `settings.redis_host` /
`settings.redis_port` raise `AttributeError`. Result: `1 passed, 1 failed (expected)`.

**PLAN.md link:** https://github.com/Rrahul0414/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
Need to confirm `redis.Redis.from_url` on the pinned `redis>=5.0.0` accepts
`decode_responses=True` and preserves the db index / credentials from the URL — I'll verify
this while implementing the fix in Week 9. Docker isn't installed on my machine, so I
reproduced the bug with a stubbed unit test rather than a live stack; the fix and its tests
are fully verifiable this way, but I'll stand up Docker before opening the PR so I can smoke-test
`GET /health` end to end.
