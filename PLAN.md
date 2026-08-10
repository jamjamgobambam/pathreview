## Solution plan

**Issue:** 
Add an API rate limiting header (X-RateLimit-Remaining) to responses — https://github.com/ascherj/pathreview/issues/86

### Understand
The existing RateLimiter in safety/rate_limiter.py calculates whether a request is allowed and how many requests remain, but this information is not currently exposed in API responses. The expected behavior is for responses to include X-RateLimit-Limit and X-RateLimit-Remaining. Requests that exceed the limit should return a 429 Too Many Requests response.

### Map
The main files involved are safety/rate_limiter.py, which contains RateLimiter.check_rate_limit() and calculates the remaining requests, and api/main.py, where FastAPI middleware is registered. The existing api/middleware/request_id.py provides an example of middleware that adds a header to responses. A new middleware component may be added under api/middleware/ to connect the rate limiter to API requests. The existing rate-limit tests are located in tests/unit/test_rate_limiter.py.

### Plan
First, add middleware that calls the existing RateLimiter.check_rate_limit() for incoming requests. Next, use the returned remaining count to add X-RateLimit-Limit and X-RateLimit-Remaining to allowed responses. If the request exceeds the limit, return 429 Too Many Requests with the rate-limit headers included. Then, register the middleware in api/main.py and verify that it works correctly with RequestIDMiddleware. Finally, add tests that verify the headers, remaining request count, and 429 behavior.

### Inputs & outputs
The fix takes an incoming API request, a request identifier, the configured request limit, the rolling window duration, and the current request count stored in Redis. For allowed requests, the normal API response should include X-RateLimit-Limit and X-RateLimit-Remaining. Requests that exceed the limit should return 429 Too Many Requests with X-RateLimit-Remaining set to 0.

### Risks & unknowns
I still need to confirm whether the identifier passed to check_rate_limit() should be a user ID, IP address, or another value. I also need to determine where the request limit and rolling window configuration should come from. Middleware ordering in api/main.py may affect whether X-Request-ID is still included on rate-limited responses. Since the rate limiter depends on Redis, I also need to determine whether the middleware tests should mock Redis or use an existing test fixture.

### Edge cases
The first request in a new window should be allowed and return the correct remaining count. The final allowed request should return X-RateLimit-Remaining: 0 without being rejected, while the next request should return 429 Too Many Requests with a remaining value of 0. Requests from different identifiers should maintain independent limits. If Redis is unavailable, the existing fail-open behavior should allow the request without causing the API to fail.