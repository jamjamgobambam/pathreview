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
