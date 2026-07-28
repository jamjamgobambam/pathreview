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