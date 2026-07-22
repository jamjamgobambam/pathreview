## Week 7 — Issue selection

**Issue link:** [link](https://github.com/ascherj/pathreview/issues/68)

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]



The /health API endpoint returns health status attributes such as status, dependencies and timestamps (`api/routes/health.py`). However, it does not account for safety events that happened in the last hour. This issue aims to add a safety_events_last_hour value to /health API endpoint result that grabs information from `safety/monitoring.py` so that operators can use /health alone to track the system's health status instead of querying the monitoring dashboard on their own too.

**Branch name:** feat/68-Add-a-safety-event-count-to-the-health-check-endpoint

**Setup confirmation:** [Y] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger

**Is This Issue Right for Me? checklist:**

I can explain what this issue is asking for in my own words, 
I can explain the problem and the expected behavior in 2–3 sentences without reading the issue, and I've located the relevant files and confirmed they exist in the codebase.
Do I understand what "done" looks like?

I can describe what the app should do (or not do) once the issue is fixed, and I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

This issue is a tier 1 issue, and it is my first open source contribution, so it is a realistic match for where I am right now. 

I've found and read the specific code the issue references, 
and I understand the surrounding code well enough to change it safely. I've found the test file for my module and read at least one test end-to-end.
When I signed up, no one was working on this issue. I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue. I also think 
the scope is realistic for Weeks 8–9?

I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline. This issue has no open blockers or dependencies on other unresolved issues.


