## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint
 #68

**Tier:** Tier 1

**Problem summary:**
The `/health` endpoint currently only reports basic service status (e.g.
whether the process is up and running), but it has no visibility into the
safety monitoring system's activity. Right now, if an operator wants to know
whether the safety system has flagged anything recently, they have to leave
the health check entirely and go query a separate monitoring dashboard. This
touches `api/routes/health.py` (the endpoint itself) and
`safety/monitoring.py` (where safety events are presumably already tracked
and would need to be queried by count over a time window). A successful fix
adds a `safety_events_last_hour` field to the health response so that
operators — and any automated alerting hitting `/health` — can see both
"is the service up" and "has the safety system been active" in one place,
without an extra dashboard lookup.

**Branch name:** fix/68-add-safety-count

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/GreyManGM/pathreview/commit/df01421d9f320723b60601d4691ce90863abef78

**Reproduction summary:**
Started the backend locally via make run and ran curl -i http://localhost:8000/health. The response already includes a safety_events_last_hour field (currently 0), which contradicts the issue's premise that this field is missing... needs investigation into whether it's fully wired up to real data or just a stub. Separately, the response returned 503 Service Unavailable because postgres and redis dependencies reported as unhealthy in the same payload.

**PLAN.md link:** https://github.com/GreyManGM/pathreview/blob/fix/68-add-safety-count/PLAN.md

**Blockers or open questions:**
- safety_events_last_hour already appears in the /health response, need to confirm whether it's reading real safety event counts from safety/monitoring.py or is a placeholder value that always returns 0. If it's a stub, the actual work is wiring it up correctly rather than adding the field from scratch.
- /health currently returns 503 locally because Postgres and Redis dependencies are unhealthy, need to confirm whether this is a local environment/config issue (e.g. services not running) or a genuine problem worth its own ticket, since it's unrelated to the safety-metrics issue but is blocking a clean "healthy" baseline to test against.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix for issue #68. In `safety/monitoring.py`, replaced the
`INCR`-based lifetime event counter with a Redis sorted set (`ZADD` with timestamp
as score), so `get_event_count(event_type, window_hours)` now performs a real
time-windowed `ZCOUNT` instead of ignoring the `window_hours` parameter. Added
`get_total_event_count()` to sum counts across all event types. In
`api/routes/health.py`, replaced the hardcoded `safety_events_last_hour: 0` stub
with a real call into `SafetyMonitor`, and made it degrade to `null` (instead of a
misleading `0`) when Redis is unhealthy. Also resolved the pre-commit failures this
introduced — ruff's `B008` warning on `Depends()`, and several mypy errors caused by
the `health_status` dict lacking an explicit type annotation and the `db` parameter
lacking a type. `pre-commit run --all-files` now passes clean (ruff, black, mypy).

**Next steps:**
- Write unit tests for `SafetyMonitor.get_event_count` / `get_total_event_count`,
  modeled on the existing `test_rate_limiter.py` pattern (mocked Redis client,
  `patch('time.time', ...)` to control timestamps)
- Add a test for `/health` covering the Redis-down case, confirming
  `safety_events_last_hour` returns `null` rather than `0` or raising
- Run the full `make test-unit` and `make test-integration` suites to confirm
  nothing else regressed
- Finalize and open the PR (description is drafted, includes manual verification
  steps for reviewers)

**Blockers:**
None currently