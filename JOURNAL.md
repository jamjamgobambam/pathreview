## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/68

**Issue title:** Add  a safety event count to the health check endpoint


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The goal of this issue is to surface safety activity directly in the /health API endpoint response so system operators can monitor recent safety events without needing to inspect external monitoring dashboards. I need to a dynamic safety_events_last_hour integer field to the health check JSON payload.
Currently, the endpoint contains a hard-coded fallback placeholder for the safety count. 

**Branch name:** fix/68-add-safety-event-count

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue understanding:** This application needs a system status check so that it reports the actual number of safety recorded recently, instead of just 0.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
This issue does not generate any errors, it just does not allow the application to run properly. It masks the fact that the actual safety metrics aren't being queried from Redis.

**PLAN.md link:** [link to PLAN.md in your fork]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed steps 1 and 2 and added an aggregation method to SafetyMonitor in safety/monitoring.py, then imported "SafetyMonitor" in "api/routes/health.py".


**Next steps:**
For the rest of the week, I will be writing a test to ensure that api/routes/health.py works properly and debugging my code.

**Blockers:**
When I try to commit my changes, I keep getting errors. I need to debug my code and determine which errors were not created by me.

---

### Check-in 2 (end of week)

**PR link:**
https://github.com/ascherj/pathreview/pull/874#issue-5066249657

**Branch:**
fix/68-add-safety-event-count

**What you built:**
I created module get_total_event_count() in safety/monitoring.py to count all safety events within a 24h window, imported SafetyMonitor and reused Redis client for safety_events_last_24h, and added tests/unit/test_health.py to ensure health.py was working properly after changes. Safety events are now logged as timestamped entries in a Redis sorted set rather than a flat counter, so safety_events_last_24h reflects a true trailing 24-hour window instead of an unknown value that could silently accumulate indefinitely under steady traffic.

**Tests added or updated:**
I created one test file: tests/unit/test_health.py. This test connects to a real local Redis instance and creates a SafetyMonitor, then logs three dummy safety events (two pii_detected, one injection_attempt). It calls the actual /health endpoint via FastAPI's TestClient and then asserts the response is 200 and that safety_events_last_24h is present and >= 3.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]
none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
I haven't received any feedback on my PR, but I did receive feedback on my contribution through Codepath. It advised me to alter my testing approach and create a unit test rather than an integration test because my test connects to a real local Redis instance and will fail in any environment where Redis isn't running.

**How you responded:**
I rewrote the test so that redis.from_url is patched via unittest.mock.patch and postgres is faked the same way, via FastAPI's dependency_overrides on get_db. fake_redis fixture creates a new instance for each test function, so nothing leaks between runs the way the shared real-Redis keys did before. I also added tests for the "no events logged" and "Redis unreachable → 503, safe fallback to 0" cases we verified separately earlier in this thread, so those are now real regression-protected tests instead of one-off scripts.

---

### Reflection

**What was harder than you expected?**
Understanding the codebase was harder than I expected. I had to spend a lot of time looking through files, then uploading them to Claude to have them explained. For the two that I worked with the fix this issue, api/routes/health.py and safety/monitoring.py, I had to go in and read them line by line. I had also never seen a health check before, so I took a lot of time understanding what the issue actually meant and what wasn't working.

**What did you learn about working in a large codebase?**
I learned how easy it can be to make a mistake that could cause damage to the code, and how important it is to fully understand what you are working with. I found myself getting a lot of errors, but didn't realize that they were occurring in code that I hadn't touched. You can't just go in and start making changes, you need to understand how everything works prior to your changes to know whether what you are changing is working or creating more problems. This is very different when compared to projects that I myself created, it takes a lot more time and effort in understanding the codebase.

**How did AI tools help — and where did they fall short?**
AI tools helped a lot when it came to understanding the codebase. I submitted certain files from the codebase, received simple summaries of what they did, and then went into those files and looked for myself at what was really happening. I found that this was the most effective way for me to learn what the files I was working on were doing.

**What would you do differently if you started over?**
At first, I was a bit overwhelmed and discourage by the size of this codebase. However, I delved deeper into what my issue meant and was able to set a scope for which files I was going to use and where my solution needed to be contained. If I were to work on another project similar to this, I would start with that approach immediately, especially since I am still not quite familiar with working with codebases this complex.

**What are you most proud of from this module?**
I am most proud of how much I was able to understand. When I did my demo during the last AI201 session, I was able to articulate how my issue affected the codebase, and how my solution functions to solve this. I sometimes worry about relying on AI too much, but I was able to reach a balance where I used AI to help me find my solution while fully understanding what I was changing.