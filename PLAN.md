## Solution plan

**Issue title:** Add an API rate limiting header (X-RateLimit-Remaining) to responses
**Issue link:** [Issue](https://github.com/ascherj/pathreview/issues/86)

### Understand
What was expected was the API already have a rate limiting feature implemented. The issue wanted to add headers to the responses so the users can know how much requests they can make before recieving a 429 status code. Since there is no rate limiting feature the headers cannot be implemented.

### Map
Related Files:
- `api/main.py`
- `core/config.py`
- `safety/rate_limiter.py`
Creating Files:
- `api/middleware/rate_limiter.py`

### Plan
1. Create a `rate_limiter.py` in the `api/middleware` directory and use `safety/rate_limiter.py`
  - Keep track of number of requests per minute and ensure user does not exceed `core/config.py` limits
    - Use both IP and JWT to keep track of requests. JWT as the main tracker, while IP as a fallback
  - Add `X-RateLimit-Remaining` and `X-RateLimit-Limit` as a response header
  - Once it exceeds the limit, return the user a 429 status code
2. Register the middleware in the app in `main.py`
  - Register `RateLimitMiddleware` before `RequestIDMiddleware` in `main.py`, so `request_id` is available when the rate limiter logs events
3. Test different types of requests to see if we can get the remaining number of requests
4. Test different types of requests to see if we can get 429 status code

### Inputs & outputs
Instead of having inputs, we keep track of how many requests a user makes per minute. Our output would be adding the counter/remaining requests the user has left before reaching the 429 status code as a response header. Our counter of requests should reset with a rolling window model and the response header should reflect the updates.

### Risks & unknowns
Currently, I may not know whether there are bugs or know whether the `safety/rate_limiter.py` works completely without bugs. I know that there are tests for it with a mock, but not sure whether they are compatiable with the API.

### Edge cases
Using both JWT as the main identifier to keep track of requests from a user, it can account for multiple instances logged in to the same account to limit requests. For the sessions that JWT is not available or for those who are not logged in, IP will be the fall back identifier to limit requests.
It will handle malformed/expired JWTs by falling back to IP (auth/authorization itself is unaffected — still enforced by the existing get_current_user dependency downstream)