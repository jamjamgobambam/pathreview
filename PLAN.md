## Solution plan

**Issue:** #86 — Add rate-limit headers to API responses  
https://github.com/ascherj/pathreview/issues/86

### Understand
The backend already enforces rate limits and tracks how many requests remain using `RateLimiter.check_rate_limit()` in `safety/rate_limiter.py`. However, clients do not consistently receive this information through HTTP response headers. Successful responses now include `X-RateLimit-Limit` and `X-RateLimit-Remaining`, but the 429 early-return path in `api/middleware/request_id.py` still does not attach these headers. The goal is for both successful and rate-limited responses to expose the same rate-limit metadata so clients can monitor usage proactively and understand why a request was blocked.

### Map
The key files and modules involved are:

- `api/middleware/request_id.py`  
  Current middleware that generates request IDs, calls the `RateLimiter`, and attaches response headers.
- `safety/rate_limiter.py`  
  Redis-backed rolling-window rate limiter that returns `(allowed, remaining_requests)`.
- Middleware registration / app setup (e.g., `main.py` or equivalent)  
  Ensures this middleware runs for all relevant API routes.
- `tests/` (middleware / API tests)  
  Existing or new tests to verify that both 2xx and 429 responses include rate-limit headers.

### Plan
1. Refactor `RequestIDMiddleware` in `api/middleware/request_id.py` so the 429 response path also includes `X-Request-ID`, `X-RateLimit-Limit`, and `X-RateLimit-Remaining` headers instead of returning a bare `JSONResponse`.
2. Keep `safety/rate_limiter.py` unchanged unless necessary, since `check_rate_limit()` already returns both the allow/deny decision and remaining quota that middleware needs.
3. Verify that both successful responses (2xx) and blocked responses (429) consistently expose `X-RateLimit-Limit` and `X-RateLimit-Remaining` with correct values.
4. Add or update tests under `tests/` to cover:
   - An allowed request returning 2xx with the rate-limit headers.
   - A blocked request returning 429 with the same headers.
5. Run `make check` and `make test-unit` and address any linting, typing, or test failures before opening or updating the pull request.

### Inputs & outputs
**Inputs:**

- Incoming HTTP request object.
- Client identifier (currently the IP from `request.client.host`, or `"unknown"` as a fallback).
- Result of `RateLimiter.check_rate_limit(identifier, limit, window_seconds)` returning `(allowed, remaining_requests)`.

**Outputs:**

- For allowed requests:
  - Normal 2xx response from the downstream handler.
  - Headers:
    - `X-Request-ID` (unique ID for the request).
    - `X-RateLimit-Limit` (configured limit for the window).
    - `X-RateLimit-Remaining` (remaining quota after the current request).
- For blocked requests:
  - 429 response with `"detail": "Rate limit exceeded. Try again later."` in the body.
  - The same three headers (`X-Request-ID`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`) attached to the response.
- No changes to the underlying Redis rolling-window logic or rate-limit configuration.

### Risks & unknowns
- The current 429 path in `RequestIDMiddleware` returns a `JSONResponse` early, so the refactor must be careful not to drop `X-Request-ID` or other headers when returning 429.
- The exact expected value of `X-RateLimit-Remaining` on blocked requests (e.g., `0` vs a value derived before the block) should be confirmed against the issue description or examples to avoid off-by-one confusion.
- Existing tests may not assert presence of rate-limit headers on 429 responses; adding new tests must follow the project’s testing patterns and may require fixtures or helpers.

### Edge cases
- A request that is the final allowed request in the current window should return 2xx with `X-RateLimit-Remaining: 0`.
- A request that exceeds the limit should return 429 and still include `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers, with values consistent with what the limiter reports.
- Multiple rapid requests from the same client should show `X-RateLimit-Remaining` decreasing in a predictable way until it reaches 0 and then produces 429s.
- Requests where `request.client` is `None` or has no `host` should still be handled gracefully (e.g., using `"unknown"`), without raising exceptions or skipping headers.
