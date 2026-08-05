## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check tries to connect using `settings.redis_host`
and `settings.redis_port`, but the `Settings` model only defines a single combined
`redis_url` field. This caused an `AttributeError` every time the Redis check ran,
so the health endpoint always reported Redis as "unhealthy" even when Redis was
working fine. I fixed it by using `redis.Redis.from_url(settings.redis_url)` instead,
which correctly parses the existing connection string. This affects the `api/routes/health.py`
file and required no changes to the `core/config.py` settings themselves.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/unt-akanksha/pathreview/commit/adf2337

**Reproduction summary:**
I called `GET /health` locally and confirmed it returned a 503 with
`"redis": "unhealthy"`, even though the Redis Docker container was running
and healthy. Checking the code showed `settings.redis_host`/`settings.redis_port`
don't exist on the `Settings` model, causing an `AttributeError` that was
silently caught and reported as an unhealthy status.

**PLAN.md link:** https://github.com/unt-akanksha/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** [not recorded — optional/ungraded]

**Blockers or open questions:**
None currently. One thing I noted in PLAN.md: fixing this surfaced an
unrelated pre-existing bug (issue #154, raw SQL string not wrapped in
`text()`), which I intentionally left out of scope for this fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Fix, tests, PLAN.md, and reproduction were already completed in Weeks 7-8. This week's focus was running the full make check/make test-unit suite to document pre-existing failures, then opening the PR.

**Next steps:**
Open the PR and fill in the full template, including documenting pre-existing failures unrelated to my change.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/628

**Branch:** fix/155-health-check-redis-host

**What you built:**
Fixed the `/health` endpoint's Redis check, which referenced nonexistent `settings.redis_host`/`settings.redis_port` fields, causing an `AttributeError` that made the health check always report Redis as unhealthy regardless of its real status. Replaced it with `redis.Redis.from_url(settings.redis_url)`, using the connection field that actually exists on the `Settings` model.

**Tests added or updated:**
Added `tests/unit/test_health.py` with two tests: one confirming Redis reports "healthy" on a successful mocked connection, one confirming a genuine connection failure is still correctly reported as "unhealthy."

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass for my changed files specifically; the full suite has 178 pre-existing lint errors and 53 pre-existing test failures in unrelated modules, documented in the PR description — my changes introduce no new failures.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No human maintainer review has been received. Per this term's course note, reviewer feedback isn't a feature in Summer 2026, so no maintainer/reviewer comments were expected. For additional context: GitHub Copilot's automated review left two comments on `tests/unit/test_health.py` (an invalid `typing.cast` usage and a test assertion that didn't verify `from_url()`'s call arguments), which I addressed in commit `9e006d1` even though this doesn't count as reviewer feedback for this assignment.

**How you responded:**
N/A — no maintainer feedback arrived. (For the automated Copilot comments noted above, I replaced the `cast()` call with an `isinstance()` check and tightened the test assertion to check exact call arguments, then replied on the PR summarizing both fixes.)

### Reflection

**What was harder than you expected?**
The environment setup in Week 7 was far harder than the assignment implied. I hit a genuine architecture-compatibility bug — ChromaDB's Docker image auto-rebuilt its native library on Apple Silicon and pulled in an incompatible numpy 2.0, crashing with `AttributeError: np.float_ was removed`. On top of that, the container's health check called `curl`, which wasn't even installed in the image, so it could never report healthy regardless of whether the server worked. Neither problem was mentioned anywhere in the course materials — it took several rounds of reading logs, reverting changes, and testing hypotheses before I found a fix (overriding the entrypoint to pin compatible versions, then swapping the health check to a Python-based one).

**What did you learn about working in a large codebase?**
Working in pathreview taught me that consistency matters more than cleverness. Before writing my fix, I read the existing try/except/logging pattern already used for the Postgres and Vector DB checks in health.py, and matched it exactly rather than writing my own style. Same with tests — I read test_review_service.py first to copy its fixture and mocking conventions before writing test_health.py. I also learned that a large shared codebase always has pre-existing problems that aren't yours to fix: when I ran the full make check/make test-unit suite, I found 178 lint errors and 53 test failures completely unrelated to my change. Learning to document that clearly — "my change introduces zero new failures" — rather than either ignoring it or trying to fix everything, felt like a genuinely professional skill I hadn't practiced before.

**How did AI tools help — and where did they fall short?**
AI tools (Claude, used throughout this project) were most helpful for pattern-matching against the existing codebase — quickly locating the right files with grep, drafting test code that matched existing conventions, and helping me interpret dense error tracebacks (like the SQLAlchemy text() issue or the numpy/Docker crash) faster than I could have alone. It also helped me catch a real gap in my own work: my first REPRODUCTION.md was written from reading the code, not from actually watching the bug fail, and questioning that assumption led me to properly revert the fix and capture the real error log. Where it fell short: GitHub Copilot's automated PR review flagged a cast() issue as "invalid under mypy," but when I actually ran mypy locally, it reported zero errors — the AI's confidence didn't match the actual tool output. I fixed the underlying code anyway since the suggestion was reasonable, but it was a reminder that AI-generated feedback still needs to be checked against ground truth, not accepted at face value.

**What would you do differently if you started over?**
I'd translate documented risks into tests immediately, not just note them. My Week 9 instructor feedback pointed out that I'd identified a malformed/empty settings.redis_url as a risk in PLAN.md, but never wrote a test for it — the risk stayed on paper instead of becoming actual coverage. Going forward, I'd treat every "risk" or "edge case" I write down as an open test-writing task, not just a note. I'd also spend less time on trial-and-error with the ChromaDB Docker fix and instead search for the specific error message earlier — I eventually did this, but only after several manual attempts (platform overrides, entrypoint tweaks) that a targeted search would have shortcut. Lastly, I'd write my JOURNAL.md selection reasoning more explicitly in Week 7 — I'd actually worked through the "Is this right for me?" checklist, but didn't write that reasoning down, and lost points for it not being visible to the grader even though the thinking happened.

**What are you most proud of from this module?**
I'm most proud of catching my own mistake in Week 8 rather than letting it slide. My first reproduction was inferred from reading code, and when asked directly "when did we actually witness this bug fail," I didn't have a good answer — so I went back, reverted the fix, triggered the real AttributeError live, captured the actual server log, and rewrote REPRODUCTION.md with real evidence instead of an assumption. It would have been easy to leave the weaker version in place since it was already committed and technically met the requirement. I'm also proud of the discipline around issue #154 — noticing a second, unrelated bug in the same file and choosing to document it instead of fixing it, even though fixing it right there would have felt satisfying. Both of those decisions came from genuinely engaging with the work rather than just checking boxes, and that's the habit I most want to carry forward.