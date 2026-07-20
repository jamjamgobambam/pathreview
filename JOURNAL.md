## Week 7 — Issue selection

**Issue link:** [Issue](https://github.com/ascherj/pathreview/issues/86)
**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Currently there is no rate limiting implemented on the API endpoint, the only limiter is the mocked Redis one that shows why the unit test passed rather than the live program. When I, the user tried to make many requests they were all 200 ok which shows why I was not able to get 429. I will need to add the middle ware of the rate limiting along with the headers to notify the users how many requests. Since its a middle ware, I dont need to go implement it for all routes as all responses will need to go through my middle ware.

**Branch name:** `fix/86/api-rate-limiting-header`

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