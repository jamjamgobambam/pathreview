## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/86

**Issue title:** Add an API rate limiting header (`X-RateLimit-Remaining`) to responses

**Tier:** [ ] Tier 1  [ X ] Tier 2  [ ] Tier 3

**Problem summary:**

Currently, there is no way to for API clients to know how many requests they have remaining before requests are blocked with a 429 error. This feature adds `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to each request so that users can track available rate limit, and requests remaining per session. This improvement affects `api/middleware` and `safety/rate_limiter.py`, and a successful implementation adds middleware that adds the headers to each request. The implementation may use similar JWT decode logic as in `middleware/auth.py` for use as the identifier arg for `safety/rate_limiter.py` and may use similar attachment logic to that in `request_id.py` to attach the rate limiter headers to the request. The implementation will also need to handle returning the 429 response, as currently there is no logic for raising and returning an appropriate response. After implementation, each request will include the new headers. 


**Checklist reasoning:**

My last two semesters of school have involved creating web apps, so I am familiar with HTTP request/response headers. I took additional time to understand the role of the middleware sections for PathReview, so while rate limiters are a new feature for me, I am familiar with the pieces involved. It is a Tier 2 issue, but I have made a few contributions to a small OSS project in the last two months, so I am no longer overwhelmed by navigating a large codebase. My contributions have been more scoped to tier 1 issues, so this issue selection represents a manageable step up from my past contributions. Given the time I have available for the remaining course term, I am confident I will be able to complete this, and potentially another issue, before the course term ends. 

**Branch name:** feat/86-ratelimit-header

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Commit documenting issue reproduction/gap.](https://github.com/hendo-21/pathreview/commit/2edcbff35be6738cc84a1db2dccc0c17a6eaee26)

**Reproduction summary:**

This issue is for a feature and not a bug fix, so I focused on illustrating the existing gap in rate limit headers. I confirmed the gap by sending `curl -iv` requests to the running dev server. Responses currently include `X-Request-ID` (from `RequestIDMiddleware`) but `no X-RateLimit-Limit` or `X-RateLimit-Remaining` headers, and repeated requests past `rate_limit_per_minute` (60) never return a `429` error code. I also wrote a failing integration test (`tests/integration/test_rate_limit_headers.py`) asserting both headers are in the response, which fails today since the middleware does not yet exist. The test hits the root endpoint `/` in `main.py` and includes the following headers in its response:

```
Headers({'content-length': '57', 'content-type': 'application/json', 'x-request-id': '94e605f5-62f0-4db3-a53b-36c0ef6829f4'})
```

**PLAN.md link:** [Link here.](PLAN.md)

**Walkthrough video (recommended):** None

**Blockers or open questions:**
- Open question: Should returning the 429 error be within the scope of this issue? As written, it implies a 429 error is returned, but that is not currently implemented and could be out of scope.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
So far this week I have completed my codebase understanding subtasks:
1. Read `core/security.py` and confirm `decode_access_token()`'s exact signature: what it returns on success, and what it raises on an invalid/expired token. Confirm what `create_access_token` sets to the user's ID.
2. Read `api/middleware/request_id.py` as the template for the new middleware and confirm the `BaseHTTPMiddleware` and `dispatch(request, call_next)` shape. Read `api/main.py` to see how middleware is added to the api.
3. Read `safety/rate_limiter.py` in full and confirm `check_rate_limit(identifier, limit, window_seconds)`'s exact return shape and whether `limit` needs to be passed in or is read internally.

**Next steps:**
The rest of the week I need to focus on implementation and verification. I haven't written any code yet. Specifically:
1. Create `api/middleware/rate_limit.py` with a `RateLimitMiddleware(BaseHTTPMiddleware)`
2. Add `RateLimitMiddleware` to `main.py`.
3. Update `tests/integration/test_rate_limit_headers.py` with additional tests.
4. Verify unit tests pass and there are no linting errors.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/654)

**Branch:** `feat/86-ratelimit-headers`

**What you built:**
Adds middleware attaching `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to every response. Enforces rate limit by returning a 429 error if client identifier exceeds rate limit. Provides api clients with information on the established rate limit and their usage remaining for the rate limit window.

**Tests added or updated:**
- `tests/unit/test_rate_limit_middleware.py` (new): identifier resolution (Bearer token with/without `sub`, malformed token, missing client) and `dispatch` behavior (allowed vs. 429-denied, header attachment, correct args passed to `check_rate_limit`), with a mocked `RateLimiter`.
- `tests/integration/test_rate_limit_headers.py` (new): coverage for remaining-count decrementing, the limit header value, 429 enforcement, invalid/sub-less Bearer tokens, and independent buckets across the seeded `user1`/`user2`/`user3` accounts.

**Self-review confirmation:** [ X ] make check passes  [ X ] make test-unit passes (no new failures on either)

**Draft PR feedback received from:** none

--- 

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ X ] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**

It was harder than I expected to construct a mental model of the app's request/response structure with the addition of Redis. This was my first time seeing Redis in an application, and it was hard for me to understand the utility as compared to say a database hosted on a server or just in-memory management. This presented a challenge given my feature (attaching rate limit headers to all requests) relies on Redis to store rate limit information on api clients via an identifier. This lack of understanding meant that in my implementation, I create a new Redis connection every time the new `RateLimitMiddleware` is initialized, rather than using a Redis client shared by all modules at the API level. I now see the value in Redis as a high performance layer for things like rate limit and health checks for checks on every HTTP request given Redis' ultra fast look up and response speed.

**What did you learn about working in a large codebase?**

It was actually very similar to other professional experiences I've had outside of software development working on existing projects. Specifically, in past experiences, I have always sought to understand the "why" behind certain decisions so that I am operating within the context of the project rather than a: trying to solve problems that have already been thoroughly thought through, and b: introducing new design patterns that just make the project more confusing. So my approach here was to be much more conservative than I might have otherwise been if developing my own personal project. I made great efforts to understand the existing design patterns and decided to model my feature after them. I also spent more time proof-reading the code and my design decisions knowing that someone would review them with a more experienced and critical eye (even so, I still see areas for improvement as described in the previous section).

**How did AI tools help — and where did they fall short?**

They helped me understand the existing architecture well, specifically the existing `safety/rate_limiter.py` and `request_id` middleware. Prompting Claude to draw an ASCII diagram of the HTTP request lifecycle was particularly helpful for me, as I had not seen this middleware design pattern before tackling this issue. Once I had my plan fleshed out, the actual code implementation via Claude was very straightforward and I had minimal edits. It didn't do a great job at explaining Redis to me however. It is possible that is because I was asking it Redis questions in the VSCode Claude extension rather than Claude chat, but it was constantly relating its answers to code snippets in the chat, which I think made it less effective at answering my general questions on Redis like "what is its utility?" and "how does it differ from a database?". I ultimately went to YouTube and watched a couple quick videos on Redis and that helped immensely. I've learned that when it comes to system design, visual aids are required for me. 


**What would you do differently if you started over?**

I would spend a little more time seeking feedback from my peers and asking them design uestions. The AI tools were great at helping me to understand specific sections of the codebase, and were generally pretty good at helping me form a mental model, but after hearing from peers in stand up it became clear to me that they were incredibly experienced and knowledgeable. For example, I bet if I had asked my class to ELI5 Redis, I would have reached for the pooled Redis client initially. Generally, it was also just very inspiring to hear from my classmates and how they approach solving problems, so if I were to do this again (likely will with 301), I would seek out those experiences more.

**What are you most proud of from this module?**

I have had a couple of PRs merged for a smaller OSS project over the last couple of months, but my efforts there have mostly been focused on bug fixes, adding regression tests for those bugs, and doing CI/CD work. All valuable experiences that I am proud of, but so far I have not contributed new functionality as I did with this feature. Implementing this new feature meant making certain system design decisions I did not have to make for those other contributions, which forced me to dig deeper into understanding the design patterns so that I could justify those decisions during code review. That work was hard, and I'm proud of how I pushed through with adversarial thinking to understand the existing system. This was my first experience seeing api middleware, and I am proud that I can now say I not only understand what it does, but have also implemented a key layer. The issue I worked on, adding rate limit headers to all api client responses, is a critical safety and usability feature that will be used by every app api client and to leave that legacy also just feels great (even if it is only a mock project).