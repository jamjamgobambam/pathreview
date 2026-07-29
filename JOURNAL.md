## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` API endpoint currently reports basic service status but doesn't include any information about the safety monitoring system. This means operators have no way to see recent safety-related activity, like how many safety events triggered in the last hour, without separately opening the monitoring dashboard. The fix adds a new `safety_events_last_hour` field to the health check response, pulling that count from the existing safety monitoring logic in `safety/monitoring.py`. This affects the `api/routes/health.py` endpoint and the safety layer of the codebase, making it easier to monitor system health from one place instead of two.
**Selection reasoning:**
I chose this as a Tier 1 issue because it's my first time contributing to a large, unfamiliar codebase, and this task has a small, well-defined scope: two named files (`api/routes/health.py` and `safety/monitoring.py`), a clear before/after behavior, and an estimated effort of 2-4 hours. It also touches a part of the app (health/monitoring) that's easier to reason about in isolation compared to a deeper architectural change, which fits my current comfort level with the codebase.

**Branch name:** fix/68-safety-event-count-health-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/salabili212/pathreview/commit/6ced81cf7b95771ee39f6cb86002d62f65df3d03

**PLAN.md link:** https://github.com/salabili212/pathreview/blob/fix/68-safety-event-count-health-check/PLAN.md

**Reproduction summary:**
Attempted to run the app locally (`docker compose up -d`, `make setup`, `make run` via Git Bash). Docker services (Redis, Postgres, vector DB) started successfully, but the backend API server did not respond (frontend logged repeated "socket hang up" errors when proxying to it), so I could not confirm the bug via a live HTTP request. Instead, I confirmed the issue directly in the source: in `api/routes/health.py`, the `safety_events_last_hour` field is hardcoded to `0` inside a comment marked "placeholder," and is never populated from `SafetyMonitor.get_event_count()` in `safety/monitoring.py`, which already tracks real event counts in Redis. This confirms the gap exists and shows exactly where it lives, even though I wasn't able to hit the live endpoint due to a local backend startup issue I'm still debugging.

**PLAN.md link:** [paste link here after you commit]

**Walkthrough video (recommended):** [optional — add if you record one]

**Blockers or open questions:**
Still need to trace where `SafetyMonitor` is instantiated in the app so I can access it from `health.py` (it currently only depends on `get_db`, not Redis). Also unsure whether to fix the "last hour" windowing bug in `get_event_count` (it's actually a flat 24-hour Redis expiry, not enforced hourly) or just document that discrepancy for now and address it during implementation.

