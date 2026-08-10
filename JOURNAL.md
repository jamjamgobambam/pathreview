## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Selection reasoning:**

I selected this Tier 1 issue because I am still becoming familiar with the PathReview codebase and wanted a focused first contribution. The issue has a clear scope limited to the health-check route and application settings, so it is a good fit for my current skill level while still giving me practice tracing configuration values through the backend.

**Problem summary:**

When we call the `GET /health` endpoint, the application crashes with an `AttributeError`. This happens because `api/routes/health.py` tries to check Redis status using `settings.redis_host`. However, the `Settings` model in `core/config.py` does not define this field, so it cannot find the host information. A successful fix will add `redis_host` to the configuration so the health check can report the Redis status correctly without any errors.

**Branch name:** fix/155-health-check-redis-settings

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Masaki0827/pathreview/commit/bd2afd230f27a299f980221308653af187130f20

**Reproduction summary:**

I reproduced the issue by starting the local services and calling `GET /health`.
The endpoint returned HTTP 503 and reported Redis as unhealthy even though the
Redis Docker container was healthy. The Redis health check failed because
`api/routes/health.py` accesses `settings.redis_host`, but the `Settings` model
in `core/config.py` defines only `redis_url`.

**PLAN.md link:** https://github.com/Masaki0827/pathreview/blob/fix/155-health-check-redis-settings/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

The health check expects separate `redis_host` and `redis_port` values, while
the existing configuration provides a single `redis_url`. I need to confirm
whether the preferred fix is to reuse `redis_url` directly or introduce
separate typed settings without creating duplicate configuration sources.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I completed the issue reproduction and solution plan. Before changing the
health-check implementation, I ran the required checks to establish a baseline.
`make check` failed during Ruff with 182 pre-existing lint errors, so its Black
and mypy steps did not run. `make test-unit` collected 428 tests: 375 passed and
53 failed, with 4 warnings. These results were recorded before implementing the
issue #155 fix.

**Next steps:**

Update the Redis health check to use the existing `settings.redis_url`, add
focused unit tests for successful and failed Redis connections, and rerun both
commands to confirm that the change introduces no new failures. Then open a
draft PR and request feedback.

**Blockers:**

The repository already has 182 lint errors and 53 failing unit tests unrelated
to issue #155. These pre-existing failures will be compared with the
post-change results and documented in the PR description.

---

### Check-in 2 (end of week)

**PR link:** [Add the submitted pull request URL]

**Branch:** `fix/155-health-check-redis-settings`

**What you built:**

I updated the Redis health check to create its client from the existing
`settings.redis_url` configuration. This removes references to the undefined
`redis_host` and `redis_port` settings while preserving URL components such as
the host, port, database, authentication, and TLS scheme.

**Tests added or updated:**

I added `tests/unit/test_health.py` with tests for a successful Redis ping and a
failed Redis connection. The two new tests pass, and the full unit test run has
the same 53 pre-existing failures observed before the change.

**Self-review confirmation:** [x] make check introduces no new failures  [x] make test-unit introduces no new failures

**Draft PR feedback received from:** Eddie (Oregon State University)

Eddie reviewed the draft PR and said that it looked good and that everything
was organized. Based on this feedback, no additional changes were required.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No official maintainer review was provided during Summer 2026. I did receive
peer feedback on my draft PR from Eddie, who said that the work looked good and
was well organized, as documented in my Week 9 entry.

**How you responded:**

Because there was no official reviewer feedback requesting a change, I did not
make any additional code changes.

---

### Reflection

**What was harder than you expected?**

Finding where the bug came from was harder than I expected. The visible problem
was the `/health` endpoint returning an unhealthy Redis status, but the cause
was a mismatch between `api/routes/health.py` and the `Settings` model in
`core/config.py`. I had to trace how Redis configuration moved through the
codebase before I could see that the health check referenced fields that did
not exist. It was also difficult to separate my change from the repository's
182 existing lint errors and 53 failing unit tests.

**What did you learn about working in a large codebase?**

I learned that I need to understand why existing code is designed in a certain
way before changing it. In my own projects, I can choose the structure and
rules, but in someone else's production code I need to follow its conventions
and avoid creating a second source of truth. For this issue, reusing the
existing `redis_url` was safer than adding duplicate host and port settings. I
also learned to run baseline checks so I can distinguish pre-existing failures
from problems caused by my contribution.

**How did AI tools help — and where did they fall short?**

AI tools helped me search unfamiliar files, understand the relationship between
the health-check route and the settings model, draft focused tests, and improve
the clarity of my documentation. However, AI could not decide the best change
from the issue description alone. I still needed to inspect the actual
codebase, reproduce the problem, compare test results before and after the
change, and confirm that using `redis_url` matched the project's existing
design.

**What would you do differently if you started over?**

I would map the relevant request and configuration flow earlier, starting from
the failing endpoint and following every setting it uses before planning a fix.
I would also run the baseline lint and unit tests immediately after setup and
record the results. That would help me identify the real scope of the issue
faster and avoid spending time investigating failures that were already in the
repository.

**What are you most proud of from this module?**

I am most proud that I learned how to explain my work specifically to a
supervisor or maintainer. Instead of only saying that I fixed a bug, I can now
describe the original behavior, identify the configuration mismatch that
caused it, explain why I chose the existing `redis_url`, and provide test
results that show what changed and what did not.
