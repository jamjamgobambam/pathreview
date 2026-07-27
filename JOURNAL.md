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


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kerrykearns/pathreview/commit/814caa161affcd92f9221923e64b3f309edb47b5

**Reproduction summary:**
I wrote a script (`reproduce_issue_68.py`) that logs safety events via `log_event`,
inspects the underlying Redis key directly, and calls `get_event_count` with two
different `window_hours` values. It confirmed the bug: both `window_hours=1` and
`window_hours=24` returned the identical count (5), because events are stored as
a single flat Redis counter with no per-event timestamps — there's nothing for
`window_hours` to filter against.

**PLAN.md link:** https://github.com/kerrykearns/pathreview/blob/feat/68-safety-event-health-check/PLAN.md

**Walkthrough video (recommended):** [leave blank, or add a Loom link if you record one]

**Blockers or open questions:**
Need to confirm with a mentor whether `safety_events_last_hour` should aggregate
across all event types in `VALID_EVENT_TYPES` or track one specific type — the
issue doesn't specify this. Also need to check if switching the Redis key from a
string counter to a sorted set requires a migration note for any existing
deployed data.