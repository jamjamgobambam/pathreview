## Solution plan

**Issue:** [Add an API rate limiting header (`X-RateLimit-Remaining`) to responses](https://github.com/ascherj/pathreview/issues/86)

### Understand
The existing `RateLimiter` in `safety/rate_limiter.py` implements and unit-tests a Redis-backed rolling window, but no production API code imports or calls it. Requests currently pass through CORS and `RequestIDMiddleware` to the route, so even 65 same-client requests all return `200` and include no `X-RateLimit-Limit` or `X-RateLimit-Remaining` headers. Expected behavior is to limit requests by client IP, report the configured limit and remaining quota on responses, and return `429` with the same headers after the quota is exhausted.

### Map
- Add `api/middleware/rate_limit.py`: adapt `RateLimiter` to the HTTP request/response lifecycle.
- Update `api/main.py`: construct/register the middleware and expose the custom headers through CORS if browser clients must read them.
- Add `tests/unit/test_rate_limit_middleware.py`: verify allowed, exhausted, and Redis-failure request paths at the HTTP boundary.
- Reuse `safety/rate_limiter.py`: existing rolling-window logic; no algorithm change is currently expected.
- Reuse `core/config.py`: `settings.redis_url` and `settings.rate_limit_per_minute` provide configuration.

### Plan
1. Create `RateLimitMiddleware`, following `RequestIDMiddleware`'s `BaseHTTPMiddleware` pattern, and derive a stable limiter identifier from `request.client.host`.
2. Call `RateLimiter.check_rate_limit()` with the configured per-minute limit before forwarding an allowed request; short-circuit denied requests with a JSON `429` response.
3. Add `X-RateLimit-Limit` and `X-RateLimit-Remaining` to both normal and `429` responses, and configure CORS exposure so frontend JavaScript can read them.
4. Register the middleware in `api/main.py` with a Redis client created from `settings.redis_url`, checking middleware order so request IDs and CORS headers remain present on rejected requests.
5. Add focused HTTP-level tests with a fake or mocked limiter for decrementing quota, the first denied request, independent client IPs, and fail-open behavior; then run the targeted and full relevant test suites.

### Inputs & outputs
Input is each HTTP request's client IP plus `settings.rate_limit_per_minute`; Redis stores request timestamps for that identifier. An allowed request continues to its route and returns the two quota headers. An exhausted identifier receives HTTP `429` with `X-RateLimit-Limit` set to the configured limit and `X-RateLimit-Remaining: 0`. A Redis error preserves the existing fail-open policy rather than making the API unavailable.

### Risks & unknowns
- `request.client.host` may identify a reverse proxy rather than the real client; trusting `X-Forwarded-For` without trusted-proxy configuration would allow spoofing, so proxy-aware identity is out of scope unless deployment settings establish trust.
- Starlette middleware registration order can cause early `429` responses to miss `X-Request-ID` or CORS processing; tests must pin down the intended order.
- The Redis client and limiter are synchronous, so direct calls in async middleware may block under load; confirm whether this project accepts the existing client model or needs thread offloading.
- `RateLimiter` fails open with a full remaining count on Redis errors, which may be misleading; preserve it for compatibility but document/test the chosen header behavior.
- “Every response” may include CORS preflight, docs, validation errors, and unhandled errors; confirm the expected exclusions before broadening scope.

### Edge cases
Handle a missing `request.client`, exactly the last allowed request (`remaining = 0`), the next request returning `429`, separate IPs receiving separate quotas, Redis being unavailable, and route-generated error responses. Ensure rate headers are non-negative integers and that denied responses retain expected request-ID/CORS headers.
