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

**Cohort ledger:** [ ] Issue added to cohort ledger