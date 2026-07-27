## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings #155

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:** The problem is that the health check endpoint in 'api/routes/health.py' tries to read a 'redis_host' attribute from the app's 'Settings' object to run its Redis probe, but this field does not exist in 'Settings.' Because of this, the endpoint breaks entirely due to the 'AttributeError'. A fix to this problem would be to update the health check to reference the right Settings field or add a field if it is missing, so '/health' will be able to report Redisok status without the endpoint breaking.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Issue Selection Notes - Checklist Reasoning 

**Part 1 - Understanding the Issue:**
I can explain the issue without re-rereading it, as I have taken time to understand it before moving onto actually solving the issue. The issue is that the health check endpoint is trying to read a 'redis_host' from 'Settings,' but either the wrong field is being references or that field was never created in the Settings model, so an error is thrown which breaks the endpoint. The relevant files include 'api/routes/health.py' and 'core/config.py,' which exist and match the description of the issue. The issue is resolved when when 'GET /health' runs without crashing and Redis status is reported. 

**Part 2 - Tier fit:**
Although I have done an open source contribution before, I chose a Tier 1 issue as I wanted a refresh on how to go about contributing to an open source project. Since the issue itself is in two files, I can focus on the larger idea, such as how to make a pull request so that the issue can eventually be closed. 

**Part 3 - Codebase Readiness:**
I located 'api/routes/health.py' and read through the 'Settings' class and figured out that 'redis_host' is not defined there, so I need to create that field in order to fix this issue. 

**Part 4 - Scopre and Time:**
Since this is a Tier 1 issue, I believe I might spend around 5 hours working on the codebase and make sure my changes do not cause other issues and test everything to make sure that the author can close their issue. 

## Week 8 - Reproduction & solution planning 

**Reproduction commit link:** 

**Reproduction summary:**
Ran the API locally and hit the GET /health endpoint. The endpoint returned 503 with "redis": "unhealthy", and the server log shows: `'Settings' object has no attribute 'redis_host'`, confirming health.py
references a field that doesn't exist on the Settings class.

**PLAN.md link:** 

**Blockers or open questions:**
A separate error also appeared when reproducting this error, a SQLAlchemny textual SQL warning. 