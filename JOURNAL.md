Week 7 — Issue selection

Issue link: https://github.com/ascherj/pathreview/issues/86

Issue title: Add an API rate limiting header (X-RateLimit-Remaining) to responses

Tier: [ ] Tier 1 [x] Tier 2 [ ] Tier 3

Problem summary:

The API currently enforces request limits, but clients have no way to know how many requests they have remaining before reaching the limit. Instead, they only find out after receiving a 429 Too Many Requests response. The existing rate limiter already calculates the remaining number of requests, but that information is not exposed in API responses. A successful fix would add the standard X-RateLimit-Limit and X-RateLimit-Remaining headers so clients can monitor their usage before exceeding the limit.

I selected this Tier 2 issue because it is challenging enough to help me learn more about middleware and request handling without requiring me to design an entirely new system. I am still becoming familiar with the PathReview codebase, but the issue has a focused scope and identifies the relevant areas of the project. The existing rate limiter already calculates the values needed for the headers, so the main task is understanding how that information moves through the middleware and response flow. This makes the issue a good match for my current comfort level because it requires codebase exploration and testing while still building on functionality that already exists.

Branch name: feat/86-rate-limit-headers

Setup confirmation: [ ] App runs locally at localhost:5173

Cohort ledger: [x] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
https://github.com/KeerthiPeruka/pathreview/commit/bba9f6123ea354734d2bd9c5afdfbdd9fe630d04

**Reproduction summary:**
I reproduced Issue #86 by running the PathReview API locally and sending a curl -i http://localhost:8000/ request. The response returned 200 OK and included the existing X-Request-ID header but it did not include either X-RateLimit-Limit or X-RateLimit-Remaining. This confirms that rate limit information is not currently exposed to API clients.

**PLAN.md link:** 
https://github.com/KeerthiPeruka/pathreview/blob/feat/86-rate-limit-headers/PLAN.md 

**Blockers or open questions:**
I still need to confirm where the existing rate limiter is called and which middleware or response layer should add the rate-limit headers.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I added rate-limit middleware that adds X-RateLimit-Limit and X-RateLimit-Remaining to API responses. I also added tests to check the headers and the 429 response when the rate limit is exceeded.

**Next steps:**
I need to finish my final checks, open a draft PR, get feedback, and submit the final PR.

**Blockers:**
The project already has some test and lint errors that are unrelated to my changes. My new tests pass and the files I changed pass the lint check.
---

### Check-in 2 (end of week)

**PR link:** 
https://github.com/ascherj/pathreview/pull/1028

**Branch:** 
feat/86-rate-limit-headers

**What you built:**
I added rate-limit headers to API responses so clients can see their request limit and how many requests they have remaining. Requests that go over the limit return a 429 response.

**Tests added or updated:**
I added tests/unit/test_rate_limit_middleware.py. The tests check that normal responses include the rate-limit headers and that requests over the limit return a 429 response with the correct headers.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** 
none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in yet.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Understanding how the existing rate limiter connected to the rest of the API was harder than I expected. I had to trace safety/rate_limiter.py, the middleware files, and api/main.py before deciding where to add the rate-limit headers.

**What did you learn about working in a large codebase?**
I learned that it is important to understand existing code before making changes. Looking at RequestIDMiddleware helped me understand how PathReview adds headers to responses and gave me a pattern to follow for my rate-limit middleware.

**How did AI tools help — and where did they fall short?**
AI tools helped me analyze existing functions in the codebase and understand how they worked before making changes. For example, I used AI to examine check_rate_limit() and RequestIDMiddleware to understand how the remaining request count was calculated and how response headers were already being added. AI was useful for explaining these existing patterns and helping me plan my implementation, but I still had to test the changes locally, debug setup issues, and verify the final behavior with curl and unit tests.

**What would you do differently if you started over?**
If I started over, I would spend more time analyzing the existing code and tests before planning my solution. This would help me understand the project’s existing patterns earlier and make it easier to decide how my changes should fit into the codebase.

**What are you most proud of from this module?**
I am most proud that I was able to work through an unfamiliar codebase and implement the rate-limit headers successfully. I also added tests for the new middleware and confirmed that the headers appeared correctly and the remaining request count decreased as requests were made.