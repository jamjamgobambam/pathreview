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
I have read through the relevant files listed in PLAN.md. Specifically, - `safety/rate_limiter.py` and `api/middleware/auth.py`. Reading these files gave me context on how the rate limiting function is called and how a response with headers is formatted, respectively. Based on this understanding, I created `api/middleware/rate_limit.py`. This file contains all of the requirements listed in PLAN.md: a `RateLimitMiddleware(BaseHTTPMiddleware)` class and a dispatch method that calls the rate limiting function and based on the answer (True or False) returns either a response or 429 error with headers in each case. This is a slight update to PLAN.md as the original diagram showed that the error response would not return headers. However, I believe it is appropriate for responses and errors to show headers for more context. Additionally, based on further codebase review, instead of creating a new integration test, I will write new tests in `tests/unit/test_rate_limiter.py` that assert the headers work as intended and build upon the existing tests. This will better follow the conventions of the repo and make for a more cohesive test suite.

**Next steps:**
Next steps are to register the RateLimitMiddleware in api/main.py following the existing conventions. Once this is done, I will create the integration tests to assert that hitting the route returns a response with headers in both the True and False case. This test will follow the structure outlined in PLAN.md.

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]