# Module 3 Journal — PathReview

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint (`api/routes/health.py`) reports the status of Postgres,
Redis, and the vector DB, and its response already includes a
`safety_events_last_hour` field — but that field is hardcoded to `0`, a leftover
placeholder that never reflects real activity. Meanwhile the safety subsystem
(`safety/monitoring.py`) already records per-type event counts in Redis (keys like
`safety:events:<type>`) and exposes `SafetyMonitor.get_event_count()`. The issue is
to connect these: populate `safety_events_last_hour` from the real safety counts
(summed across the monitor's valid event types) so operators can watch safety-system
activity straight from `/health` without opening the monitoring dashboard. A
successful fix replaces the constant `0` with a live, Redis-backed count and handles
errors gracefully so a Redis hiccup never breaks the health check itself.

**Branch name:** fix/68-health-safety-event-count

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/hspb2024/pathreview/commit/ce8240b109224f6e5c54429b45ac1ab3b77c363e

**Reproduction summary:**
I added a unit test (`tests/unit/test_health_safety_events.py`) that records three
safety events through the real `SafetyMonitor` (backed by an in-memory fake Redis) and
then calls the actual `/health` endpoint. The monitor reports 3 events, but
`safety_events_last_hour` from `/health` comes back as `0` (`assert 0 == 3` fails) —
confirming the endpoint hardcodes the value and never reads the safety counters. One test
passes (the safety layer records counts) and the reproduction test fails, pinpointing the
bug at the hardcoded `0` in `api/routes/health.py`.

**PLAN.md link:** https://github.com/hspb2024/pathreview/blob/fix/68-health-safety-event-count/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
The Redis counters are cumulative per-type with a 24-hour TTL, so a literal "last hour"
window isn't supported by the current data model — I need to decide whether to ship the
cumulative sum with a documented caveat (my lean, keeps it Tier 1) or introduce
time-bucketed keys (larger scope). Separately, `health.py` references
`settings.redis_host`/`redis_port`, which don't exist on `Settings` (only `redis_url`) —
a pre-existing bug I'll route around and flag to the maintainer.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from PLAN.md. Sub-task 1 done: added
`SafetyMonitor.get_total_event_count()` in `safety/monitoring.py`, which sums the
per-type counters across `VALID_EVENT_TYPES` and returns 0 on error. Sub-task 2 done:
wired `api/routes/health.py` to build a Redis client from `settings.redis_url`,
instantiate `SafetyMonitor`, and set `safety_events_last_hour` to the real total instead
of the hardcoded `0`. Sub-task 4 done: the Week 8 reproduction test now passes, and I
added edge-case tests (no events → 0, Redis unavailable → graceful 0).

**Next steps:**
Run the full `make check` / `make test-unit`, document any pre-existing failures, open a
draft PR for peer feedback, then mark it ready for review.

**Blockers:**
None blocking. I verified behavior via the real endpoint in unit tests (fake Redis)
rather than a full `make run`, since local Docker is still being finalized — the unit
tests exercise the actual `health_check` code path, so this is sufficient to validate the
fix.

---

### Check-in 2 (end of week)

**PR link:** _(PR opened against `ascherj/pathreview` — URL pasted here on submission)_

**Branch:** `fix/68-health-safety-event-count`

**What you built:**
The `/health` endpoint now reports `safety_events_last_hour` from the real safety
subsystem instead of a constant `0`. A new `SafetyMonitor.get_total_event_count()` sums
the per-type Redis counters, and the endpoint reads it via a client built from
`settings.redis_url`. The count is best-effort: if Redis is unavailable the endpoint logs
and reports `0` rather than failing the health check.

**Tests added or updated:**
`tests/unit/test_health_safety_events.py` (4 tests): the safety layer records counts;
`/health` surfaces the real summed count; a zero baseline with no events; and graceful
degradation to `0` when Redis is down. All pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> In this codebase "passes" means *no new failures* (the suite has documented
> pre-existing failures — see below). My changed files are clean: `ruff` and `black`
> report **0 new issues** on my additions (health.py holds its 4 pre-existing ruff
> findings; monitoring.py its pre-existing black trailing-comma and 3 ruff findings);
> `mypy` is clean on `safety/monitoring.py` and adds **0 new errors** to `health.py`
> (11 pre-existing, identical to `origin/main`, including the `settings.redis_host`
> bug). `make test-unit`: my 4 tests pass and total failures did **not** increase
> (53 → 52); the ~52 failures / 31 errors are pre-existing in unrelated modules
> (`test_semantic_chunker`, `test_structural_chunker`, etc.) and no existing test
> touches the files I changed.

**Draft PR feedback received from:** none
