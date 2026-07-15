## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health endpoint already advertises a `safety_events_last_hour` field, but it is currently hardcoded to zero. That means operators cannot tell whether the safety layer has been active recently, even though the app has monitoring hooks for safety events. A successful fix would make the health check report a real count instead of a placeholder so the endpoint reflects the actual safety system state.

**Selection notes:**
This fits the checklist for a first issue because it is small, isolated, and easy to verify. It stays inside the health/monitoring path rather than crossing into auth, ingestion, or the frontend, so the blast radius is low. I also avoided a stale tracker item where the current code already had the requested behavior.

**Branch name:** fix/68-health-check-safety-event-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/RadRebelSam/pathreview/commit/2269a0a9d9eb9ef623ba88b2ced13104fc3124cd

**Reproduction summary:**
I added two unit tests in `tests/unit/test_health_safety_events.py`. The first drives `SafetyMonitor.get_event_count` (via an in-memory Redis stand-in) and confirms it returns real, non-zero counts after events are logged. The second calls the `/health` endpoint with a mocked DB and observes that `safety_events_last_hour` comes back as `0` no matter what — proving the endpoint never consults the monitor and just returns the hardcoded placeholder. While reproducing, I also noticed the endpoint's Redis health check references `settings.redis_host`, which doesn't exist (config only defines `redis_url`) — an adjacent bug I've noted in PLAN.md but scoped out of this fix.

**PLAN.md link:** https://github.com/RadRebelSam/pathreview/blob/fix/68-health-check-safety-event-count/PLAN.md

**Walkthrough video (recommended):** [not recorded yet]

**Blockers or open questions:**
The main open question is the "last hour" semantics: `get_event_count` ignores its `window_hours` argument and the Redis counters use a 24h TTL, so the count is cumulative rather than a true rolling hour. I need to confirm with the maintainer whether to relabel the field or implement hourly bucketed keys before Week 9.
