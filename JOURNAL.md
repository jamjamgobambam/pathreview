## Week 7 — Issue selection

**Issue link:** [Issue](https://github.com/ascherj/pathreview/issues/86)
**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Currently there is no rate limiting implemented on the API endpoint, the only limiter is the mocked Redis one that shows why the unit test passed rather than the live program. When I, the user tried to make many requests they were all 200 ok which shows why I was not able to get 429. I will need to add the middle ware of the rate limiting along with the headers to notify the users how many requests. Since its a middle ware, I dont need to go implement it for all routes as all responses will need to go through my middle ware.

**Branch name:** `fix/86-api-rate-limiting-header`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### **Selection Notes:**

**Do I understand which part of the app is affected?**

Yes. This touches `api/middleware/` (currently only `request_id.py` and an 
auth middleware exist — no rate limiting middleware), `safety/rate_limiter.py` 
(the unused `RateLimiter` class), and `core/config.py` (unused 
`rate_limit_per_minute` setting). I confirmed all three files exist and read 
their contents directly.

**Do I understand what "done" looks like?**

Yes. Before: authenticated requests to any endpoint always return 200, no 
matter how many are sent in a short window, and no response includes rate 
limit information. After: once a client exceeds [X] requests in [window], 
they receive a 429 response; every response (whether allowed or blocked) 
includes `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers so clients 
can proactively back off before hitting the limit.

**Can I find the relevant code?**

Yes. I read `RateLimiter.check_rate_limit()` in full, including its Redis 
sorted-set logic and fail-open behavior on Redis errors. I also read 
`RequestIDMiddleware` in `api/middleware/request_id.py` as the structural 
template for how middleware is written and registered in this app, and 
traced `main.py` to see exactly where and how `add_middleware()` calls are 
wired in.

**Scope:**

I have worked with other large codebases before like Thonny and Idle Python Editors, so I believe this issue will be addressed within the next couple of weeks.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [Link to Commit Documenting the Reproduced Issue](https://github.com/ascherj/pathreview/commit/cc6aa2d6556f14164dedfd9f994bd92b8dcf7655)

**Reproduction summary:**
I went to `http://localhost:8000/docs#/reviews/list_reviews_endpoint_reviews_get` and logged in with `user1.example.com` on the lock icon to generate a curl command of the reviews. Then I used the terminal with the following commands. Where the key is the token generated with the curl command.
``` bash
TOKEN=<Key>

for i in {1..1000}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8000/reviews?page=1&page_size=20" \
    -H "Authorization: Bearer $TOKEN")
  echo "$code"
done > status_code.log
```
Once it's done running, I ran `sort status_code.log | uniq -c` and it showed `1000 200` in the terminal.

These commands prints the status codes of 1000 GET requests made for the reviews page and prints it out to a `status_code.log` file then the `sort status_code.log | uniq -c` finds different instances of status codes. `1000 200` means that there are 1000 instances of 200 status codes and shows no 429 meaning a rate limiter has not been implemented for the API. I also ran the test suite for `tests/unit/test_rate_limiter.py`, it shows that all tests passed, but upon further inspection, it only tests on a mocked Redis rather than actual requests from the API.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
So far, the JWT rate limiter and the tests for the JWT are implemented along with the headers that were needed from the issue. X-RateLimit-Limit and X-RateLimit-Remaining headers are added to every API response.

**Next steps:**
Implement the IP ratelimiting as the fallback when JWT tokens are malformed or expired. Unit testing will are also needed to verify that it reaches to the IP fall back or manual testing.

**Blockers:**
When implementing the IP rate-limit, how would it limit requests from the login or register pages?

---

### Check-in 2 (end of week)

**PR link:** [Link to pull request](https://github.com/ascherj/pathreview/compare/main...kevku:pathreview:fix/86-api-rate-limiting-header?expand=1)

**Branch:** `fix/86-api-rate-limiting-header`

**What you built:**
Added `RateLimitMiddleware` (`api/middleware/rate_limiter.py`), which wires 
the existing (previously unused) `RateLimiter` class into every API request. It resolves a rate-limiting identifier from the JWT's `sub` claim when a valid bearer token is present, falling back to the client's IP address for unauthenticated or invalid/expired tokens. It attaches `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to every response, and returns a 429 with those same headers once the caller exceeds `rate_limit_per_minute` within the rolling 60-second window.

**Tests added or updated:**
`tests/unit/test_rate_limiter_middleware.py` (new file, 11 tests): covers 
valid-JWT requests under/over the limit, remaining-count decrementing 
across repeated calls, per-user identifier isolation, IP fallback for 
missing/malformed/non-Bearer/invalid Authorization headers, IP-based 
isolation across different clients, IP-path over-limit denial, and JWT 
taking priority over IP when both are available. `RateLimiter`'s own 
internal logic (rolling window, per-identifier isolation, fail-open on 
Redis error) is unchanged and already covered by the existing 
`tests/unit/test_rate_limiter.py`, so this suite mocks `RateLimiter` 
directly rather than re-testing it.

**Self-review confirmation:** 
* [x] make check passes  

make check` (lint) introduces zero new errors — confirmed the same 
182 pre-existing errors present on a fresh clean pull remain unchanged 
after my changes; my two new files pass `ruff check` cleanly on their own

* [x] make test-unit passes

`python -m pytest tests/unit/test_rate_limiter_middleware.py 
tests/unit/test_rate_limiter.py`, 30 passed  
Prior to changes was 53 failed, 375 passed, 1 warnings in 5.00s
After Changes was 53 failed, 386 passed, 2 warnings in 5.00s 
As a result no changes caused pre-existing tests to fail. 

**Draft PR feedback received from:** none