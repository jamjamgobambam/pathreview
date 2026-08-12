# Journal

## Issue #68 — `/health` always reports `safety_events_last_hour: 0`

**Branch:** `fix/68-safety-event-count-health-check`

### Reproduction steps

Checked out the pre-fix state of the two relevant files (parent commit `d5f196d`,
before the fix in `c1aa518`) and exercised them directly — no live Postgres/Redis/
Docker required, using a minimal in-memory stand-in for `redis.Redis`:

```
git show d5f196d:safety/monitoring.py > old_monitoring.py
git show d5f196d:api/routes/health.py  > old_health.py
```

Then logged 5 `pii_detected` events through the old `SafetyMonitor` and called
`get_event_count()` with both a near-zero window and a 24h window.

### Confirmed bugs

1. **`get_event_count(event_type, window_hours)` ignores `window_hours` entirely.**
   Old implementation was `self.redis.get(key)` against a flat `INCR` counter with a
   fixed 24h TTL — the parameter was accepted but never used (its own docstring even
   said "not enforced here; for reference"). Reproduced: after logging 5 events,
   `get_event_count(window_hours=0.0000001)` returned `5`, identical to
   `get_event_count(window_hours=24)` — a window that should have excluded
   everything returned the same count as a 24-hour window.

2. **`health_check()` hardcodes `safety_events_last_hour` to the literal `0`.**
   `SafetyMonitor` was never imported or instantiated in `api/routes/health.py`, so
   the field could never reflect real activity regardless of how many safety events
   occurred.

3. **The ad hoc Redis client in the old health dependency check reads
   `settings.redis_host` / `settings.redis_port`, which don't exist on `Settings`**
   (`core/config.py` only ever defined `redis_url`). Reproduced:
   `hasattr(Settings(), "redis_host")` and `hasattr(Settings(), "redis_port")` are
   both `False`. That means the old `redis.Redis(host=..., port=...)` call raised
   `AttributeError` on every single request, silently caught by the bare
   `except Exception`, so `/health` always reported `redis: "unhealthy"` even when
   Redis was actually up and reachable.

### Status

Fixed in `c1aa518` (`fix(api): surface safety event counts in /health`), same
branch: added a shared `core.redis.get_redis()` dependency using `settings.redis_url`,
reworked `SafetyMonitor` to use a Redis sorted set so `window_hours` is actually
enforced, and wired `SafetyMonitor` into `/health`. See
`docs/plans/safety-events-health-metric.md` for the full design writeup, and
`tests/unit/test_health.py` / `tests/unit/test_monitoring.py` for regression coverage
added alongside the fix.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Qianyu2021/pathreview/commit/5e1950f

**Reproduction summary:**
Checked out the pre-fix version of `api/routes/health.py` and `safety/monitoring.py`
(parent commit `d5f196d`) and ran them directly: logging 5 events and calling
`get_event_count()` with a near-zero window vs. a 24h window both returned `5`,
confirming `window_hours` was never enforced, and confirmed `health_check()` hardcoded
`safety_events_last_hour` to `0` regardless of any logged events.

**PLAN.md link:** https://github.com/Qianyu2021/pathreview/blob/fix/68-safety-event-count-health-check/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five steps from `PLAN.md` are implemented and committed in `c1aa518`
(`fix(api): surface safety event counts in /health`): added `core/redis.py`
with a shared `get_redis()` dependency, reworked `SafetyMonitor.log_event` /
`get_event_count` to use a Redis sorted set so `window_hours` is actually
enforced, added `get_total_event_count`, wired `SafetyMonitor` and
`Depends(get_redis)` into `health_check`, fixed the `db.execute("SELECT 1")` →
`db.execute(text("SELECT 1"))` bug, and whitelisted `fastapi.Depends` for
ruff's B008 check.

**Next steps:**
Add regression tests for both files (no prior coverage existed), confirm
`make check` and `make test-unit` show no new failures versus the
pre-existing baseline, then open a draft PR for peer/mentor review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/Qianyu2021/pathreview/pull/1

**Branch:** `fix/68-safety-event-count-health-check`

**What you built:**
`/health` now reports a real rolling one-hour count of safety events instead
of a hardcoded `0`. A shared `get_redis()` FastAPI dependency backs a
`SafetyMonitor` instance wired into the route, which tracks events in a Redis
sorted set (scored by timestamp) so `window_hours` is enforced via
`ZREMRANGEBYSCORE` + `ZCOUNT` rather than the old flat, unwindowed counter.

**Tests added or updated:**
`tests/unit/test_monitoring.py` (new) — covers window eviction/inclusion,
custom windows, Redis-error fallback to `0`, and `get_total_event_count`
summation. `tests/unit/test_health.py` (new) — covers the happy path, safety
count summing across event types, a Redis failure during the safety-count
lookup degrading to `0` (not a 500), and Redis/Postgres-down still returning
503. Neither file had prior coverage.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both commands show pre-existing failures in unrelated modules — e.g.
`test_bias_detector.py`, `test_pii_scrubber.py`, `test_review_service.py`,
159 pre-existing lint errors elsewhere — that predate this branch and are
untouched by this change. No new failures introduced.)

**Draft PR feedback received from:** none yet — PR just opened, reviewer requested: ascherj


## Week 10 — Iteration & reflection

### Reflection

**What was harder than you expected?**
the open source section is harder than I expected. reading the codebase, finding the 
related section, and fixing the bugs is harder than I thought. 
I learnt from the class that, it is common that fixing a bug and getting it integrated to the codebase takes a long time. 
Under one bug, there are multiple people's comments and want to contribute to it. Knowing the issue, and getting familiar with the section of the codebase is important. It is a long term work.  

**What did you learn about working in a large codebase?**
I have experience of working in a large codebase during my internship too. understanding the structure, and knowing where to find the code, file, functions related to the issue is the key. Understanding the relationships between the files can help find the issues and solving the issues. 

**How did AI tools help — and where did they fall short?**

AI does help a lot. It has saved me lots of time to understand the code, and has given me the guidance, and helped me learn the things I didn't know and didn't understand. It is a good teacher and assistant.

**What would you do differently if you started over?**
I would have tried to understand the concepts from a high level first, and given me more time to dig more into different topics.

**What are you most proud of from this module?**

I keep learning new things, practicing, and be consistant. 