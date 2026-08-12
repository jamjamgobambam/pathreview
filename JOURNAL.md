## Week 7 — Issue selection
**Issue link:** https://github.com/ascherj/pathreview/issues/68
**Issue title:** Add a safety event count to the health check endpoint
**Tier:** Tier 1
**Problem summary:**
The /health API endpoint returns the basic service status but not surface safety metrics. Operators currently have to use the monitoring dashboard manually to track system activity. Implementing a safety_events_last_hour field in the health check response will expose this metric directly, requiring data flow modifications between safety/monitoring.py and api/routes/health.py.
**Branch name:** fix/68-health-endpoint-safety-count
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning
**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/2578ff266e9aabf44706292441ea468c8d028520)
**Reproduction summary:**
Requested the `/health` endpoint locally and verified the response omits the `safety_events_last_hour` metric entirely.
**PLAN.md link:** (https://github.com/10-49/pathreview/blob/fix 68-health-endpoint-safety-count/PLAN.md)
**Walkthrough video (recommended):** 
**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Took notes on current environment status pre-working on the issue and began implementing the fix. Updated `api/routes/health.py` to call `get_safety_events_last_hour()` and return the `safety_events_last_hour` key in the JSON, outputting to `null` if the monitoring fails.

**Next steps:**
Add a comprehensive unit test for the new monitoring logic and health route responses. confirm `make check` and `make test-unit` pass, and finalize PR.

**Blockers:**
My workstation moved so trying to setup the repository on two different machines was a large hassle, and syncing work between them properly. Version mismatches on imported tools causing issues, docker/setup issues plagued the beginning of the working process. 

**PR link:**: https://github.com/ascherj/pathreview/pull/923 

**Branch:** `fix/68-health-endpoint-safety-count`

**What you built:**
Added a `safety_events_last_hour` metric to the `/health` endpoint response. Implemented a timestamped event logging using sets sorted by Redis in `safety/monitoring.py` (calcuating rolling-window style event totals for safety health events). Updated the `api/routes/health.py` file to execute the query and output `null` if the monitoring service fails, keeping the standard health check status.

**Tests added or updated:**
Added `tests/unit/test_monitoring.py` and `tests/unit/test_health.py` to cover rolling-window, edge boundaries, failure, and response formatting.

**Self-review confirmation:** Make check and make unit-test passes. Verified that pre-existing failures observed count as 176 in make check and 53 in make test-unit. New implementation and unit tests introduced no new failures. 

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** No

**Summary of feedback:**

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Setting up the project to work in my local environment was a lot more tedious than I had expected it to be. Setup took as much if not more time than it took to actually implement the feature/bugfix into the codebase. 

**What did you learn about working in a large codebase?**
There is a lot more to the process of working in a large codebase than just writing and uploading code, I had to refactor and re-evaluate my implementation to make sure it met contribution guidelines, as well as passing the linter and other evaluations to greenlight the push to the branch before I could even make a pull request. 

**How did AI tools help — and where did they fall short?**
AI tools helped a lot during the implementation of the bugfix for both understanding overarching concepts of how the repository functioned, understanding the functions I was interacting with to implement the fix, and understanding errors in my code that were being caught in the linter. 

**What would you do differently if you started over?**
I would take more time to learn about the specific linting and evaluation metrics for git so that my implementation doesn't get interrrupted by me spending a lot of time trying to rewrite code to pass evaluation when I could have written the code while being more aware of how the linter would evaluate it from the start.

**What are you most proud of from this module?**
I am the most proud of experiencing something new and learning about the processes of git, as well as the nature of open source contributions. 