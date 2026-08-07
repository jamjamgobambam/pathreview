## Solution plan

**Issue:** [Add rate limiting per IP address in addition to per user](https://github.com/ascherj/pathreview/issues/70)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
Currently, the `RateLimiter` component in `safety/rate_limiter.py` only tracks one identifier per request (which is the authenticated user ID). Consequently, unauthenticated requests or a single IP making requests across multiple user IDs can bypass the rate limit. The expected behavior is that the rate limiter tracks both the user ID (if available) and the IP address. If the IP address exceeds the request limit within the time window, further requests from that IP should be blocked, regardless of the user ID.

### Map
Which files, functions, or modules are involved?
- `safety/rate_limiter.py`: `RateLimiter.check_rate_limit()` needs to be modified to accept an `ip_address` parameter and check both the primary identifier and the IP address.
- `tests/unit/test_rate_limiter.py`: Add unit tests (and update existing ones) to test the new IP tracking behavior.

### Plan
What are the steps to fix this issue?
1. Modify the `check_rate_limit` signature in `RateLimiter` to accept an `ip_address: str` parameter.
2. In `check_rate_limit`, check the rate limit against the `ip_address` key in Redis first. If it exceeds the limit, return `(False, 0)`.
3. If the IP check passes, then check the `identifier` (e.g., user ID). If it exceeds the limit, return `(False, 0)`.
4. If both checks pass, record the request against both the IP address key and the identifier key in Redis.
5. Update `tests/unit/test_rate_limiter.py` to fix the `test_reproduce_ip_rate_limit_gap` test and pass `ip_address` to all existing test cases.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
- **Input:** `identifier` (str | None) and `ip_address` (str).
- **Output:** Returns a boolean indicating if the request is allowed, along with remaining requests. 
- **Change:** The Redis store will now hold two sorted sets for each request (one for IP, one for user).

### Risks & unknowns
What could go wrong? What are you still unsure about?
- Double counting: If we add to both the IP key and the user key, each request takes 2 Redis writes instead of 1. We must make sure it scales well or use a pipeline.
- If a route doesn't pass the IP address properly, it might cause the rate limit to fail or crash.

### Edge cases
What inputs or states should your fix handle gracefully?
- `identifier` is `None` (unauthenticated requests): Should only track and limit by IP address.
- Redis failures: Like before, we fail open and return `(True, limit)` if Redis is down.