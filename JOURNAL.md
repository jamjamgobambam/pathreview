# PathReview Contribution Journal

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1      [ ] Tier 2      [ ] Tier 3

**Problem summary:**
The `/health` endpoint currently includes a `safety_events_last_hour` field, but the value is only a hard-coded placeholder and does not reflect actual safety activity. The existing safety monitoring module records events such as PII detection, prompt-injection attempts, filtered content, detected bias, and rate limiting in Redis. A successful change will connect the health endpoint to those stored metrics so operators receive a meaningful recent-event count while preserving the endpoint's existing dependency checks. The affected code is primarily in `api/routes/health.py` and `safety/monitoring.py`.

**Selection notes - "Is this right for me?" checklist:**
- The issue is labeled Tier 1 and identifies two relevant Python files, so the scope is bounded enough for a first contribution.
- The current behavior is easy to observe because the health response always reports zero safety events.
- The repository already has a `SafetyMonitor` abstraction and Redis-backed counters, so the change can extend existing patterns rather than introduce an unrelated monitoring system.
- The phrase "last hour" needs clarification because the current counters use a 24-hour expiry and do not enforce a one-hour window. I will confirm the intended counting design before implementation.
- The change should include focused tests covering aggregation, no-event behavior, and monitoring failures.

**Branch name:** `feat/68-safety-event-health-count`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
