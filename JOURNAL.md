## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/86)

**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses
 #86

**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3

**Tier Reasoning:**
I have contributed to open source projects before and have some familiarity with APIs. Due to this, I believe that the Tier 2 issues with tags referencing "api" will be a good fit for me. I can commit to the 8-12 hour time commitment that is expected for a Tier 2 issue.

**Problem summary:**
Currently the API rate limiter throws a 429 error when the client has exceeded their limit. However, the client doesn't know how many requests they have left before hitting or exceeding the limit, making it difficult to navigate and use the API. A successful fix will add "limit" and "remaining" headers to each response that the client receives from the API. The relevant directory and file for this fix are api/middleware/ and safety/rate_limiter.py.

**Branch name:** feat/86-add-rate-limit-header

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (https://github.com/ddingi09/pathreview/commit/9d2a2d30f20fc1678a59176b75c0dfea15e63a77)

**Reproduction summary:**
As this issue is a feat, not a fix, in order to reproduce the issue I read through each of the files in the api/middleware directory and the safety/rate_limiter.py file. I asked Claude to explain how these files interact with each other and how the current rate limit route is constructed. I found that currently a 429 error is not thrown anywhere in the repo, this will be a feature that I will implement following the established error structure in api/middleware/auth.py. Additionally, rate_limiter.py currently computes the requests that the user has left. I can use this number as a header in the updated return statement. I will add the two new headers as a new api/middleware file and register them in api/main.py following the structure of request_id.py.

**PLAN.md link:** (https://github.com/ddingi09/pathreview/blob/feat/86-add-rate-limit-header/PLAN.md)

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have read through the relevant files listed in PLAN.md. Specifically, - `safety/rate_limiter.py` and `api/middleware/auth.py`. Reading these files gave me context on how the rate limiting function is called and how a response with headers is formatted, respectively. Based on this understanding, I created `api/middleware/rate_limit.py`. This file contains all of the requirements listed in PLAN.md: a `RateLimitMiddleware(BaseHTTPMiddleware)` class and a dispatch method that calls the rate limiting function and based on the answer (True or False) returns either a response or 429 error with headers in each case. This is a slight update to PLAN.md as the original diagram showed that the error response would not return headers. However, I believe it is appropriate for responses and errors to show headers for more context. Additionally, based on further codebase review, instead of creating a new integration test, I will write unit tests in `tests/unit/test_rate_limit_middleware.py` that assert the headers work as intended and follow the strucutre of existing tests in `test_rate_limiter.py`. This will better follow the conventions of the repo and make for a more cohesive test suite.

**Next steps:**
Next steps are to register the RateLimitMiddleware in api/main.py following the existing conventions. Once this is done, I will create the unit tests to assert that the route returns a response with headers in both the True and False case. This test will follow the structure outlined in PLAN.md.

**Blockers:** none

---

### Check-in 2 (end of week)

**PR link:** (submitted PR)[https://github.com/ascherj/pathreview/pull/580]

**Branch:** [`feat/86-add-rate-limit-header`](https://github.com/ddingi09/pathreview/tree/feat/86-add-rate-limit-header)

**What you built:**
I created a new `api/middleware/rate_limit.py` file that executes the check_rate_limit function in `safety/rate_limiter.py`. If the rate limiter function returns True and the remaining request count, the middleware returns a Response with X-RateLimit-Limit and X-RateLimit-Remaining headers to inform the user how many of the allocated request have been used. If the rate limiter function returns False and 0, the middleware returns a 429 error with same headers. This middleware was registered in api/main.py so that it would be integrated into the app.

**Tests added or updated:**
I added `tests/unit/test_rate_limit_middleware.py` to assert that X-RateLimit-Limit and X-RateLimit-Remaining are included in responses and errors. To do so, I built a minimal TestClient and patched the return value of `check_rate_limit` to return false or true. Afterward, I asserted that the correct headers are returned in each case.

**Self-review confirmation:** [✅] make check passes  [✅] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [✅] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
Understanding the architecture of a route within the app was harder than I expected. I read through multiple files to understand where the headers would be returned, how they were included in the response, and what a "dispatch" method is in relation to the middleware.

**What did you learn about working in a large codebase?**
I learned the importance of pushing small, specifc commits so that tracking my work was easier in relation to the larger codebase. I also learned the importance of first reading through the codebase, specifically any README files or routes, to understand the current structure before making any changes.

**How did AI tools help — and where did they fall short?**
AI assistance was very helpful with understanding the structure of the codebase and explaining unfamiliar parts. For example, AI was very helpful when I was trying to understand the middleware and how `request_id.py` could use the dispatch method to add the `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers. I needed to go beyond the context that AI gave me to fully read through the files and understand the structure from my own perspective.

**What would you do differently if you started over?**
If I were to start over, I would spend even more time reading through the codebase. I think that if I spent more time reading through files that weren't necessarily linked to my PR, it would be helpful to gather more context about the codebase and support my ability to make the PR.

**What are you most proud of from this module?**
I'm most proud of quickly onboarding onto a large codebase and understanding how headers work in routes. This was my first time adding headerst to an API route and I enjoyed learning all of the different components that went into this task.