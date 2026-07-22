## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint currently doesn't report how many safety events
have occurred recently, making it hard to spot spikes in safety-related
issues at a glance. The goal is to add a `safety_events_last_hour` field to
the health response so this can be monitored without digging through logs.
While investigating `safety/monitoring.py`, I found that the existing
`get_event_count()` function accepts a `window_hours` parameter but doesn't
actually use it — events are tracked as a single running Redis counter per
event type with a flat 24-hour TTL, not as timestamped entries. So a
successful fix requires adding real time-bucketed counting (e.g. per-hour
keys or a timestamped sorted set) to `monitoring.py`, updating `log_event`
to write to it, and then wiring the new count into the health endpoint in
`api/routes/health.py`.

**Branch name:** feat/68-safety-event-health-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger