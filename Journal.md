## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/154#issuecomment-5039403002]

**Issue title:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The issue is that the database health check or probe within the ap/routes/health.py route is passing a raw SQL string plainly rather than explicitely marking the expression or string using sqlalchemy.text() so SQLAlchemy can correctly interact with the expression. Since SQLAlchemy doesn't expect a raw string, it raises an ArgumentError instead. As a result, the /health endpoint is incorrectly reported as unnavailable even though the connection is working properly or is reachable. A successful fix would wrap the string with the sqlalchemy.text() call within the api/routes/health.py file at the "SELECT 1" portion would allow the Get /health api endpoint call using curl to be successful and return the appropriate health records.

**Branch name:** [fix/154-DB-Probe-SQL-Input-Error]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection_Reasoning**
I've never contributed to an opensource project and many of the formalities are new to me so I wanted to choose a issue that was self-contained. It's also my first time navigating such a large codebase so I wanted to choose a tier 1 problem since they only affect a small number of files, therefore, it gives me the chance to slowly ease open source contribution. I found that the issue was well defined and I could accurately predict the affected files or where to start looking, I've also handled past debugging issue much like this on so I feel especially confident with this nature of issue. In addition to this, I don't have much time these following weeks so I wanted to choose a problem that was more adjusted with my expected work output.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ascherj/pathreview/commit/af8dc3124ef7bf5db6ce9f784760c8f0adc86b3a)

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
Using the established testing client offered by fastapi and pytest, we are able to run the test file under tests/integration/test_get_health.py listed under test_health_endpoint. This test simply calls the get health endpoint and verifies whether it is successful or produces an error upon contacting or establishing a connection with it. This can also be replicated by running the app by using make run, and using gitbash to run the curl http://localhost:8000/health command which will return with the error description.

**PLAN.md link:** (https://github.com/ascherj/pathreview/commit/2c5e3233325e113df8a1969205af1595b0aff47f)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I imported and integrated the text() wrapper offered by SQLAlchemy during update 2.xx for raw SQL text within the health.py file within the route folder. After doing so, I 
had to run the text I implemented and I sadly learned that the assertion within the test_get_health.py file in the test/integration folder was failing, following the 
procedure I detailing slightly in the Plan.md, I investigated the cause of this error to determine the cause of it to evaluate whether the cause of it was from the solution I implemented.
Doing so, I learned that this was an error or situation caused by a separate bug that is highlighted in issue 43.

**Next steps:**
[What are you working on for the rest of the week?]
Ask for clarification from TA's or the slack tech help channel whether I should fix the error and confirm if the error is in fact already existing or present.

**Blockers:**
[Anything slowing you down? Or leave blank.]
I must wait for clarification from a TA or the tech help channel to know whether I should try to implement a fix that is blocking the get_health probe from passing or if I should narrow the 
scope of the test I implemented to specifically target the error caused by SQLAlchemy. This would be the most likely situation given that the cause of the error is already documented as a seperate
issue but I still wanted to be entirely sure that I can continue with my work.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/888

**Branch:** fix/154-DB-Probe-SQL-Input-Error

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]
I simply updated or altered the api/routes/health.py file to import the text() wrapper from the SQLAlchemy library and integrate it within the db.execute to wrap the "Select 1" SQL command so it can be 
successfully executed. SQLAlchemy update 2.xx enforces that all raw SQL commands must be wrapped by their text() wrapper to ensure maintainability for the database.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
To ensure that this change corrected the error this fix is targeting, I also implemented a test within test/integration/test_get_health.py that asserts that the response from the get_health route does not return a status of 503 that is more commonly attributed to SQLAlchemy errors. I updated this test case after encountering issue #54 which made it impossible to receive a successful status of 200 without implementing a fix for it, I then needed to change the scope of this test from asserting that it returns 200 to only checking that it doesn't return a status of 503.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** ["none"]
