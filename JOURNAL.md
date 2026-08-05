# Week 7 — Issue selection

- **Issue link**: https://github.com/ascherj/pathreview/issues/155
- **Issue title**: Health check references settings.redis_host, which does not exist on Settings
- **Tier**: [x] Tier 1  [ ] Tier 2  [ ] Tier 3

## Problem summary:
The application's health check endpoint is failing because it attempts to access `settings.redis_host`, which is currently undefined in the `Settings` model within `core/config.py`. This causes an `AttributeError` when calling `GET /health`. I will resolve this by adding the missing `redis_host` field to the `Settings` configuration to allow the health check to function correctly.


## Selection Reasoning:
I selected this Tier 1 issue because it is a contained bug that allows me to get familiar with the project's configuration management without needing to refactor core business logic. It provides a clear, actionable path for my first contribution while helping me understand how the project handles settings.

- **Branch name**: fix/155-redis-host-settings
- **Setup confirmation**: [x] App runs locally at localhost:5173
- **Cohort ledger**: [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning
- **Reproduction commit link:** [\[reproduction commit \]](https://github.com/theoneineed/pathreview/commit/35e6f8c593ceed76407a20ca468a3c1dbbe20765)
- **Reproduction summary:**
I started the local server using `make run` and hit the backend API directly using `curl http://localhost:8000/health`. While the endpoint returned a JSON response, the application logs explicitly threw the error: `redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`, confirming the missing configuration field.
- **PLAN.md link:** https://github.com/theoneineed/pathreview/blob/fix/155-redis-host-settings/PLAN.md
- **Walkthrough video (recommended):** didn't make a video.
- **Blockers or open questions:** None.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
I successfully reproduced the bug and traced it to missing fields in `core/config.py`. I implemented the fix by adding `redis_host` and `redis_port` to the `Settings` class, matching the existing Pydantic `Field` patterns. Running the server locally confirms the `AttributeError` is gone and the Redis health check now passes.
**Next steps:**
I need to verify that `make check` and `make test-unit` have not introduced any new failures beyond the pre-existing baseline. After that, I will commit my changes, push to my branch, and open the Draft Pull Request.
**Blockers:**
None.


### Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/513#event-28827910108
**Branch:** fix/155-redis-host-settings
**What you built:**
I fixed an `AttributeError` in the `/health` endpoint that crashed the application. Based on peer feedback, I refactored `api/routes/health.py` to directly use the existing `settings.redis_url` via `redis.Redis.from_url()`, keeping the configuration DRY. Additionally, I added missing typing annotations to the health route (`dict[str, Any]`) to satisfy `mypy` and resolved pre-existing linter errors caught during the pre-commit phase.
**Tests added or updated:**
I created `tests/unit/test_health.py` and added `test_health_endpoint_resolves_without_crash` which uses a FastAPI `TestClient` to verify the endpoint returns a valid 200 or 503 status code instead of a 500 Internal Server Error.
**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
**Draft PR feedback received from:** @fperezrugama (implemented their suggested from_url refactor and route testing)



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review. There was comment on it for the draft PR but nothing for the actual PR.

**Summary of feedback:**
There has beeen no review made on the PR

**How you responded:**
No changes made as no review for the PR was available. But, there was a review in draft PR which I found quite insightful as it was an easier solution to the problem than the one I had implemented. I changed my approach, implemented the suggestion from the reviewer, and pushed the changes to github.
---

### Reflection

**What was harder than you expected?**
My experience with python is in completely different domain than the work I was working on for this work. Interacting new tools such as redis, json and such tools which I do not normally use was a bit challenging in the beginning. 


**What did you learn about working in a large codebase?**
The scale of the work this time was definitely bigger than anything I had worked on before. So, it was a bit intimidating in the beginning. But with the help from claude and gemini, I was able to walk through the codebase. I learned how to navigate toml files, how to track the bug to the file relevant to it rather than getting stuck in the files that have nothing to do with the issue I was working on.

**How did AI tools help — and where did they fall short?**
I used claude and gemini to help me through the issue. When exposing the genAI agent to the whole project, it would tend to hallucinate sometimes but when I created a new session and would only pass it relevant information, that issue got resolved.

**What would you do differently if you started over?**
As it was a learning opportunity for me, I am glad about the mistakes I made as I got to learn from them. But, I would probably choose some issue to solve, that was close to the type of work I had done before to reduce the time spent on this work.

**What are you most proud of from this module?**
Although it is just a mock project, I am glad that I made some contributions to an open source work. This is something I always wanted to do, but would be intimidated by due to the size of open source software work in github. Hopefully, this work will lead to more open source contributions from me in the future.