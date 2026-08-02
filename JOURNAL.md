## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint in `api/routes/health.py` runs a raw SQL string, "SELECT 1", directly against the database to verify connectivity. Under SQLAlchemy 2.x, raw SQL strings must be explicitly wrapped in `sqlalchemy.text()`, or the driver raises an `ArgumentError` instead of executing the query. As a result, the health check currently reports the database as down even when it's fully reachable, since the probe itself is failing before it can return a real status. To fix the issue, the query needs to be wrapped in `text("SELECT 1")` so the probe executes correctly and the endpoint accurately reflects the database's actual connection state.

**Branch name:** fix/wrap-health-check-sql-in-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue Claim Checklist**

*Understanding the Issue*
- [x] Can explain the issue in my own words (2-3 sentences), without re-reading it
- [x] Located the relevant files/area of the codebase
- [x] Can describe a concrete before/after of what "done" looks like

*Reasoning*
The issue is well-documented and straightforward. A raw "SELECT 1" string is being passed directly to SQLAlchemy 2.x, which requires raw SQL to be wrapped in `text()`. This causes the `/health` endpoint to report the database as down even when it's reachable. Done looks like: `GET /health` returns a healthy DB status instead of raising `ArgumentError`.

---

*Tier Fit*
- [x] Tier matches my experience level
- [x] Not choosing a higher tier just to challenge myself

*Reasoning*
I picked a Tier 1 issue because this would be my first contribution to an open source project. I don't have the experience for a Tier 2 or Tier 3 issue yet, so this tier will be challenging enough.

---

*Codebase Readiness*
- [x] Found and read the specific function/route the issue references (not just the file)
- [x] Understand the surrounding code well enough to sketch a rough fix plan without looking anything up
- [x] Found the relevant test file and read at least one test end-to-end

*Reasoning*
The fix is confined to one function in `api/routes/health.py`. I looked at the route handler to confirm this is the only change needed there. I don't believe there is a corresponding test from looking through the codebase.

---

*Scope and Time*
- [x] Checked issue comments + cohort ledger Claims count, comfortable with how many others are on it
- [x] Estimated the time needed and confident I can finish by the Week 9 deadline
- [x] Confirmed no open blockers/dependencies on unresolved issues

*Reasoning*
This is a small fix with clear reproduction steps already given in the issue, so I firmly believe I can finish by the Week 9 deadline. No blockers or dependent issues were mentioned in the issue description.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue](https://github.com/ascherj/pathreview/commit/ebfcd4d341f052fba9cb23eba5eed696e6e32c4b)

**Reproduction summary:**
I reproduced the issue by calling the health endpoint via a curl command `curl -i http://localhost:8000/health`. As expected from the issue description, despite being able to login using a default user, the response reported an unhealthy database connection: `{"status":"unhealthy","dependencies":{"postgres":"unhealthy","redis":"unhealthy","vector_db":"healthy"}`.

**PLAN.md link:** [link to PLAN.md](https://github.com/mar1s0l/pathreview/blob/fix/wrap-health-check-sql-in-text/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have not implemented any of the steps from my PLAN.md. I may have more work ahead of me as I am considering writing a unit test for the endpoint I am modifying to make sure it works as expected reliably.

**Next steps:**
I am going to iteratively complete the plan I outlined in my PlAN.md. As I make changes, I will run `make test-unit` to make sure I am not breaking any functionality. Once I complete my change and ensure that my fix "done" as outlined in the 7 steps shown in class, I will create and submit a PR.

**Blockers:**


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/538

**Branch:** `fix/wrap-health-check-sql-in-text`

**What you built:**
This fix wraps the raw `"SELECT 1"` string in `sqlalchemy.text()` in the Postgres health check `api/routes/health.py` (SQLAlchemy 2.x requires textual SQL to be explicitly declared this way) and fixes the Redis check to use `redis.Redis.from_url(settings.redis_url)` instead of nonexistent `redis_host`/`redis_port` settings. Together these resolve two bugs that caused `/health` to report `"unhealthy"` and return a 503 even when Postgres and Redis were both fully reachable. Unit tests were added to cover the happy path, each dependency failing independently, and a regression guard against the raw-SQL-string bug recurring.

**Tests added or updated:**
There were no tests for the /health endpoint. I created `tests/unit/test_health.py` to house tests to verify that GET /health correctly reports each dependency's (Postgres, Redis, vector DB) status independently and returns the appropriate 200/503 response, including a regression test guarding against the raw-SQL-string bug that caused false "unhealthy" reports.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

After my fix, `make check` actually reduced the number of errors. The total count dropped to 179 from 183. `make test-unit` produced the same failed and passed test counts before I added tests for the fix. Afterwards, my added tests were all marked passed.

**Draft PR feedback received from:** "none"
