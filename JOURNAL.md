# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68
<!-- TODO: double-check this opens to the right issue before submitting -->

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The `/health` endpoint in `api/routes/health.py` already includes a
`safety_events_last_hour` field in its response, but the value is hardcoded
to `0` — it's a placeholder that never reads real data. Meanwhile,
`safety/monitoring.py` already has a working `SafetyMonitor` class whose
`get_event_count()` method reads real per-event-type counts (PII detections,
prompt-injection attempts, content filtering, bias flags, rate limiting)
out of Redis, incremented by `log_event()` whenever the safety layer catches
something. The health check just never calls it. A successful fix wires
`SafetyMonitor` into the health route — giving it a Redis client, pulling
real counts across the tracked event types, and replacing the hardcoded `0`
with that real number — so anyone watching `/health` sees actual safety
event volume instead of a count that always reads zero.

**Scope reasoning (from the "Is this right for me?" checklist):**

- Touches two files I can already point to (`api/routes/health.py`,
  `safety/monitoring.py`) — small, well-bounded change.
- The hard part (counting events) is already built; this is wiring, not new
  design — good for a first issue.
- No new external dependencies — Redis client pattern already exists in the
  file (see the Redis health check a few lines above the placeholder).
- Open question I'll need to resolve in Week 8: should the field report one
  summed count across all event types, or a breakdown per type? Worth asking
  in the issue thread or checking for maintainer guidance before implementing.

**Branch name:** fix/68-safety-event-health-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [823a04d](https://github.com/joshuawlee/pathreview/commit/823a04d12398b3765a753c6790b124f89c0cbc38)

**Reproduction summary:**
Added `tests/unit/test_health.py`, which calls `health_check()` directly
with a mocked Redis client seeded with a real `pii_detected` count of 5
(simulating what `SafetyMonitor.log_event()` would have written). The
assertion `response["safety_events_last_hour"] != 0` fails with `0 != 0` —
confirming the field is hardcoded and never reads the real counts that
`SafetyMonitor.get_event_count()` already exposes.

**PLAN.md link:** [PLAN.md](https://github.com/joshuawlee/pathreview/blob/fix/68-safety-event-health-check/PLAN.md)

**Walkthrough video (recommended):** [not recorded yet]

**Blockers or open questions:**
Still need to resolve whether `safety_events_last_hour` should be one
summed count across all `SafetyMonitor.VALID_EVENT_TYPES` or a per-type
breakdown — no guidance found yet in the issue thread. Also found a
second, pre-existing bug in the same function (`settings.redis_host`/
`redis_port` don't exist on `Settings`, only `redis_url` does) that I'll
likely need to touch while wiring up a real Redis client for the actual
fix.
