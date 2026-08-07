## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is that the The /health API endpoint returns service status but doesn't surface safety metrics. What is missing is a safety_events_last_hour field to the health check response. The fix would be adding a safety_events_last_hour field to the endpoint so that the so operators can monitor safety system activity without querying the monitoring dashboard. It affects safety/monitoring.py and api/routes/health.py part of the codebase. 

**Branch name:** https://github.com/proy19/pathreview/tree/fix/68-Add-a-safety-event-count-to-the-health-check-endpoint

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/e7f5832e3ecb9e2baa20782a788c2384aa696a34 

**Reproduction summary:**
I inspected health.py and confirmed safety_events_last_hour was hardcoded to 0 with a comment noting it was a placeholder, never calling into SafetyMonitor. Since I didn't have a live Redis/Postgres environment to hit /health directly, I reproduced the underlying logic gap in isolation — stubbing redis and structlog and driving SafetyMonitor.log_event() / get_event_count() directly — which confirmed the old single-key-with-resetting-TTL design had no way to return a true "last hour" count; it could only return an unbounded rolling total.

**PLAN.md link:** https://github.com/proy19/pathreview/blob/fix/68-Add-a-safety-event-count-to-the-health-check-endpoint/PLAN.md 


**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- **`safety/monitoring.py`** — Reworked `SafetyMonitor` to store events in hourly Redis buckets (`safety:events:{event_type}:{YYYYMMDDHH}`, 48h expiry) instead of a single counter with a resetting TTL. Rewrote `get_event_count(event_type, window_hours)` to sum the buckets covering the requested window, and added `get_total_event_count(window_hours)` to aggregate counts across all event types.

- **`api/routes/health.py`** — Wired `SafetyMonitor` into the `/health` endpoint: it's now instantiated with the same Redis client used for the Redis dependency check, and `safety_events_last_hour` is set from `get_total_event_count(window_hours=1)` instead of a hardcoded `0`. If Redis is unreachable, the field returns `None` rather than a misleading `0`.

**Next steps:**
My next steps are adding tests to check my changes. I want to add the following tests:

- **`tests/test_safety_monitoring.py`** — Unit tests for the bucketed counting logic (correct bucket keys, expiry, per-type isolation, window inclusion/exclusion, Redis-failure handling).

- **`tests/test_health.py`** — Endpoint tests verifying `/health` wiring: the field comes from `SafetyMonitor`, reuses the existing Redis client, and degrades gracefully (`None`) on Redis/SafetyMonitor failures.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/871

**Branch:** https://github.com/proy19/pathreview/tree/fix/68-Add-a-safety-event-count-to-the-health-check-endpoint

**What you built:**
My fix populates the previously hardcoded safety_events_last_hour field in the /health endpoint with a real count, by reworking SafetyMonitor to store events in hourly Redis buckets (safety:events:{event_type}:{YYYYMMDDHH}) instead of a single counter with a resetting TTL. health.py now instantiates SafetyMonitor with the same Redis client used for the Redis dependency check and calls a new get_total_event_count(window_hours=1) method, which sums the relevant hourly buckets across all event types; if Redis is unreachable, the field returns None instead of a misleading 0.

**Tests added or updated:**
**`tests/test_safety_monitoring.py`** — Unit tests for `SafetyMonitor` (`safety/monitoring.py`), using a dict-backed mock Redis client and frozen time. Covers:
- `log_event` writes to the correct hourly bucket key and sets the 48h expiry
- same-type events in the same hour accumulate; different types get separate keys
- unknown event types are ignored and never written to Redis
- Redis failures in `log_event`/`get_event_count` are caught, not raised
- `get_event_count` correctly includes/excludes hours based on `window_hours` — the core regression test for the old unbounded-rolling-total bug
- `get_total_event_count` sums correctly across all five event types, respects the window, and isn't broken by one flaky event type

**`tests/test_health.py`** — Endpoint tests for `/health` (`api/routes/health.py`) using FastAPI's `TestClient`, with `SafetyMonitor` mocked so these stay focused on wiring rather than duplicating the logic above. Covers:
- `safety_events_last_hour` reflects `SafetyMonitor.get_total_event_count(window_hours=1)`, not a hardcoded value
- `SafetyMonitor` is constructed with the same Redis client used for the Redis dependency check
- Postgres down → 503 with `postgres: unhealthy`
- Redis down → `safety_events_last_hour` is `None` (not `0`), and `SafetyMonitor` is never constructed
- missing `vector_db_url` → `unavailable`, doesn't flip overall status
- `get_total_event_count` raising mid-request → degrades to `None` instead of a 500

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review has come in

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Setting up my local environment and reproducing the issue was harder than expected. I kept running into errors. I eventually 

**What did you learn about working in a large codebase?**
I learned that that when you contribute in a large codebase, there's a different syntax in code that you must follow. It also can be time consuming to set it up on your local environment. 

**How did AI tools help — and where did they fall short?**
AI tools helped me my understand the issue and which steps I would require to solve it. They fell short when it comes to actually understanding the codebase. AI would often give suggestions that doesn't align with the exising codebase, like using a package that doesn't exist or not following the proper coding format. 

**What would you do differently if you started over?**
I would've definitely added more tests, specifically integration tests. 

**What are you most proud of from this module?**
I am proud of being able to fix my issue and opening a complete PR. I also learned a lot about open source contribution. 