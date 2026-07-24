# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` API endpoint reports whether core dependencies (Postgres, Redis, vector DB) are up, but its `safety_events_last_hour` field is hardcoded to `0` — it's a placeholder that never reflects real safety activity. The app already tracks safety events (PII detections, prompt-injection attempts, content filtering, rate limiting, etc.) in the `SafetyMonitor` class, but the health endpoint never reads those counts, so an operator can't see recent safety activity without opening a separate monitoring dashboard. A successful fix wires the health endpoint to the real safety-event data so `/health` reports how many safety events actually occurred recently. This touches the API layer (`api/routes/health.py`) and the safety monitoring module (`safety/monitoring.py`).

**Branch name:** fix/68-health-check-safety-event-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes — "Is this right for me?":**

- **Scope is contained.** The issue names exactly two files — `api/routes/health.py` and `safety/monitoring.py` — and is labeled Tier 1 / good-first-issue with an estimated 2–4 hours of effort, which fits a first contribution to a large codebase.
- **I understand the problem.** The response field already exists but is a hardcoded `0` placeholder, and the data source (`SafetyMonitor`, which counts events in Redis) already exists too — so the core of the work is *wiring* the two together rather than building something from scratch.
- **There's a real wrinkle I've already spotted.** The issue asks for events in the "last hour," but `SafetyMonitor` doesn't enforce a one-hour window (its Redis counter has a 24-hour expiry and the `window_hours` argument is explicitly "not enforced"), and it counts one event type at a time. So I'll need to sum across all event types and decide how to handle the time window — I'm flagging this for PLAN.md.
- **Low blast radius.** The change is additive to a monitoring field and doesn't alter core request/review flows, so the risk of breaking existing behavior is low.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jenvrosen/pathreview/commit/7db760c2c5e17f156240c88a17f8b6ad928c72fd

**Reproduction summary:**
Wrote `tests/unit/test_health_safety_events_reproduction.py`, which records safety events through `SafetyMonitor` (proving the data exists and is countable) and then invokes the real `/health` endpoint. The endpoint returns `safety_events_last_hour: 0` even though safety events occurred — confirming the field is a hardcoded placeholder disconnected from `SafetyMonitor`. The desired-behavior assertion is marked `xfail(strict)` so CI stays green while the bug is documented.

**PLAN.md link:** https://github.com/jenvrosen/pathreview/blob/fix/68-health-check-safety-event-count/PLAN.md

**Walkthrough video (recommended):** *(not recorded yet)*

**Blockers or open questions:**
The issue asks for events in the "last hour," but `SafetyMonitor` doesn't actually enforce a one-hour window — its Redis counter has a 24-hour TTL and the `window_hours` argument is "not enforced." Going into Week 9 I need to decide whether to implement true one-hour windowing (e.g. Redis sorted sets keyed by timestamp) or keep the existing rolling counter and make the field's meaning honest. Planning to get mentor input before choosing.
