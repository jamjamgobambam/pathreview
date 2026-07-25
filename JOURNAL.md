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
