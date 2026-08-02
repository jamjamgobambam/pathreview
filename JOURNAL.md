## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68#issue-4117410262

**Issue title:** Add a safety event count to the health check endpoint


**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In api/router/health.py file, the health check endpoint does not include a safety events count. There is a placeholder variable (safety_events_last_hour) which doesn't read the actual data.
But, in safety/monitoring.py file, there is a function that reads the safety events count from the database. I need to write helper functions to read the data from the database and update the health check endpoint to show the actual safety events count instead of a constant zero value.

**Branch name:** feat/68-add-safety-events-count-to-health-check

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 – Reproduction & solution planning

**Reproduction commit link:** https://github.com/ronypy/pathreview/commit/e499e4bba779b5d3af10d62d9d06f7089b1b701e

**Reproduction summary:**
Logged three safety events (`pii_detected` ×2, `injection_attempt` ×1) through the real `SafetyMonitor` in `safety/monitoring.py` using an in-memory Redis stand-in, then confirmed `SafetyMonitor.get_event_count()` reported a total of 3 while the `/health` endpoint's logic in `api/routes/health.py` (lines 25 and 75–80) still returned `safety_events_last_hour: 0`. The counter and the endpoint are disconnected — the endpoint hardcodes `0` instead of reading the counters that already exist.

Reproduction steps:
1. Instantiate `SafetyMonitor` and call `log_event()` for a few event types.
2. Read the counts back via `get_event_count()` → returns the real totals (3).
3. Compare against the endpoint field, which is hardcoded to `0` in `api/routes/health.py` → mismatch confirms the bug.

**PLAN.md link:** https://github.com/ronypy/pathreview/blob/feat/68-add-safety-events-count-to-health-check/PLAN.md

**Walkthrough video (recommended):** _[not recorded]_

**Blockers or open questions:**
The field is named `safety_events_last_hour`, but `get_event_count()` ignores its `window_hours` argument and `log_event()` sets a 24-hour Redis TTL — so the underlying counters aren't actually scoped to one hour. Going into Week 9 I need to decide whether to keep the name and document the approximation, or implement a true rolling 1-hour window (per-minute buckets / sorted sets).

## Week 9 – Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core of the fix from `PLAN.md`. Added `SafetyMonitor.get_total_event_count()` in `safety/monitoring.py` (sub-task 1) — it sums the per-type Redis counters across `VALID_EVENT_TYPES`. Wired it into `api/routes/health.py` so `safety_events_last_hour` reports the real total instead of a hardcoded `0` (sub-task 2). While wiring it, I found the existing Redis check referenced `settings.redis_host`/`redis_port`, which don't exist in `core/config.py` (only `redis_url` does), so I switched to `redis.Redis.from_url(settings.redis_url)` and reuse that one client for both the Redis health check and the safety count.

**Next steps:**
Finish sub-task 3 (fail-safe on Redis outage) and sub-task 4 (tests): unit tests for the new aggregate method and an endpoint-level test proving the wiring. Then run `make check` / `make test-unit` and document the pre-existing baseline before opening the PR.

**Blockers:**
Decided to keep the `safety_events_last_hour` name and document the window approximation (per the Week 8 open question) rather than build a true rolling 1-hour window — that's a larger change and out of scope for issue #68. Noted as a follow-up.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/558

**Branch:** `feat/68-add-safety-events-count-to-health-check`

**What you built:**
The `/health` endpoint now reports the real number of recorded safety events instead of a constant `0`. A new `SafetyMonitor.get_total_event_count()` aggregates the per-type counters already stored in Redis, and the endpoint builds a `SafetyMonitor` from the shared Redis client to populate `safety_events_last_hour`. If Redis is unavailable the count falls back to `0` and the endpoint stays responsive (Redis is separately reported `unhealthy`).

**Tests added or updated:**
`tests/unit/test_monitoring.py` (new, 11 tests) — covers `log_event`, `get_event_count`, and the new `get_total_event_count` (summing, empty state, per-type error isolation, and an end-to-end log→count check). `tests/unit/test_health_endpoint.py` (new, 3 tests) — asserts the endpoint reports the real total, reports `0` with no events, and degrades gracefully to `0` + 503 when Redis is down.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
_(Interpreted per the assignment's pre-existing-failures rule: the repo has a documented baseline of 53 failing unit tests and 175 ruff errors in unrelated modules. My branch adds 14 passing tests and introduces zero new failures — baseline 53 failed / 375 passed → 53 failed / 389 passed. My four changed files are clean under all three tools: `ruff` passes, `black --check` passes, and `mypy` on the two changed source files went from 11 errors → 0 (the annotations and `redis.from_url` switch cleared them). So my change makes things strictly better, not worse.)_

**Draft PR feedback received from:** none (peer review happens in Slack; will request a draft-PR review there before marking ready)
