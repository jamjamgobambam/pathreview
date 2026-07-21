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
