## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/155]

**Issue title:** [Health check references settings.redis_host, which does not exist on Settings]

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The core issue for this bug is that the `redis_host` field is missing from `Settings` in config.py, which raises an AttributeError when it's referenced within api/routes/health.py. While investigating, I also found that `settings.redis_port` is referenced in the same block and is also missing from `Settings`  meaning fixing only `redis_host` wouldn't fully resolve the crash. Additionally, the broad `except Exception` in the health check silently catches this error, so instead of visibly failing, the endpoint just reports `redis: unhealthy`  a false negative regardless of Redis's actual status. A good fix could look like using `redis.Redis.from_url(settings.redis_url)` instead of relying on separate host/port fields.]




**Branch name:** [fix/155-redis-host-attributeerror]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger





## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/Jwalcott02/pathreview/commit/ba91c39]

**Reproduction summary:**
[Reproduced by temporarily reverting to the pre-fix code and calling curl http://localhost:8000/health, which triggered redis_health_check_failed error=\"'Settings' object has no attribute 'redis_host'\" in the server logs confirming the AttributeError occurs exactly as described in the issue.]

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]




## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Implemented the fix (redis.Redis.from_url() replacing the broken host/port kwargs), added the first test coverage for /health (2 passing tests), and established a documented baseline of pre-existing lint/type/test failures unrelated to this issue.

**Next steps:** Open the PR, write the full PR description, and complete Check-in 2.

**Blockers:** None — ready to open the PR.
---

#### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/590]
**Branch:** fix/155-redis-host-attributeerror
**What you built:** Fixed the /health Redis check by using redis.Redis.from_url(settings.redis_url) instead of nonexistent redis_host/redis_port fields; added first-ever test coverage for the endpoint (2 passing tests covering healthy and unhealthy Redis states).
**Tests added or updated:** tests/unit/test_health.py — new file, 2 tests.
**Self-review confirmation:** [x] make check passes (no new failures introduced) [x] make test-unit passes (no new failures introduced)
**Draft PR feedback received from:** none (submitted directly due to time constraints)




## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review feedback received (not a feature in Summer 2026 per course note).

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Environment setup took far longer than anticipated. PowerShell doesn't support the Makefile's Unix syntax (wait, trap, &), so I had to switch to Git Bash mid-week, and Docker Desktop needing to be manually started each session caused repeated, confusing connection errors that looked like code bugs but were actually just infrastructure not running.

**What did you learn about working in a large codebase?**
Fixing the actual bug was small, but understanding it safely required reading multiple files (health.py, config.py) and running mypy and tests before and after to prove I hadn't broken anything else. In a codebase with 179 pre-existing lint errors and 53 pre-existing test failures, "my change is correct" isn't enough; you have to prove "my change didn't make things worse."

**How did AI tools help — and where did they fall short?**
AI was most useful for explaining unfamiliar tooling (git rebase, PowerShell vs Bash differences, mypy error messages) and for structuring tests I hadn't written before. It fell short on the actual judgment calls, like choosing redis.Redis.from_url() over adding new Settings fields, which required understanding this specific codebase's conventions, not something AI could decide for me.

**What would you do differently if you started over?**
I'd check docs/SETUP.md before troubleshooting environment issues by hand. I spent significant time fighting PowerShell and Makefile incompatibilities that the setup guide explicitly warned about upfront.

**What are you most proud of from this module?**
Finding that redis_port was also missing from Settings, beyond what the original issue text mentioned, and that the health check's broad exception handling was silently reporting false "unhealthy" statuses even when Redis was actually fine.