## Solution plan
**Issue:** [Add rate limiting per IP address in addition to per user](https://github.com/ascherj/pathreview/issues/70)

### Understand
The repo has a `RateLimiter` in `safety/rate_limiter.py`, but it is not called from the request path. Because of this, unauthenticated traffic is effectively unbounded and authenticated traffic is not actually limited. I need to add enforcement in middleware and make it usable for both anonymous and authenticated users while preserving fail-open behavior.

I will implement a two layer plan: every request gets an IP limit, and authenticated requests also get a user limit. The middleware will return 429 only when one of these checks is exceeded. Redis errors will stay warn-and-continue.

### Map
- `api/middleware/rate_limit.py` (new): `RateLimitMiddleware` with client IP extraction, optional user extraction, and limit checks.
- `api/middleware/request_id.py`: no logic changes, but ordering reference for expected headers.
- `api/main.py`: create Redis client with short timeouts, register middleware stack, and wiring for middleware constructor args.
- `core/config.py`: add/keep `rate_limit_trust_proxy: bool = False`; continue using `rate_limit_per_minute`.
- `tests/unit/test_ip_rate_limiting_repro.py`: promote existing xfail to strict assertion and add real app wiring checks with `app.build_middleware_stack()` + `TestClient`.
- `tests/unit/test_rate_limit_middleware.py`: add typed unit tests for IP/user keys, middleware behavior, timeout-safe fail-open, and header contract.

### Plan
1. I will implement `RateLimitMiddleware` in `api/middleware/rate_limit.py` with `dispatch` enforcing:
   - IP key on every non-exempt request, e.g., `ip:<address>`.
   - User key only when token/user resolution succeeds, e.g., `user:<user_id>`.
   - Shared budget source `settings.rate_limit_per_minute` and fixed 60-second window.
   - Redis exceptions logged as warning and pass-through.
   - `check_rate_limit` invoked via `starlette.concurrency.run_in_threadpool` so sync Redis calls do not block the event loop.

2. I will extract client identity with `request.client.host` and support proxy opt-in:
   - default: ignore `X-Forwarded-For` (`rate_limit_trust_proxy = False`).
   - when trusted proxy mode is enabled: use the first clean `X-Forwarded-For` value.
   - fallback `ip:unknown` if host is unavailable.

3. I will create Redis in `api/main.py` as `redis.Redis.from_url(settings.redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)` and pass it into middleware wiring.
   - I will register middleware in this order:
     1. `RateLimitMiddleware`
     2. `CORSMiddleware`
     3. `RequestIDMiddleware`
   - Since `add_middleware` wraps by prepending, runtime stack becomes RequestID outermost, CORS next, rate limit innermost.

4. I will exempt `/health` from limiting and keep `/auth/login`, `/auth/register`, profiles, and reviews protected by the IP/user checks.
   - On breach, I will return:
     - status `429`
     - `{"detail": "Rate limit exceeded"}`
     - `Retry-After: 60`
     - `X-RateLimit-Limit: <rate_limit_per_minute>`
     - `X-RateLimit-Remaining: <remaining_count>`

5. I will strengthen tests:
   - In `test_ip_rate_limiting_repro.py`, replace xfail with hard assertions:
     - app wiring check through middleware chain
     - `app.build_middleware_stack()` succeeds
     - a real `TestClient` request to a public route returns `200` when Redis is unreachable (fail-open path is exercised)
     - `OPTIONS` preflight response contains `X-Request-ID` so middleware order is validated for CORS preflight behavior
   - add focused middleware tests for Redis timeout exceptions and prefixing behavior.

### Inputs & outputs
Inputs:
- `settings.redis_url` for Redis connection.
- `settings.rate_limit_per_minute` for shared limit value.
- `settings.rate_limit_trust_proxy` to decide `X-Forwarded-For` usage.
- `RateLimiter.check_rate_limit` with `(identifier, limit, window_seconds)`.

Outputs:
- Redis-backed rate enforcement for unauthenticated and authenticated traffic.
- `429` responses with defined JSON body and headers.
- `Retry-After` fixed to `60` seconds.
- `X-RateLimit-Limit` and `X-RateLimit-Remaining` populated in rejection responses.
- Middleware ordering outcome: `RequestIDMiddleware` outermost, then CORS, then rate limiter.
- Redis exceptions are logged and requests continue.
- Tests now assert real middleware construction and runtime behavior instead of strict xfail.

### Risks & unknowns
- The hardcoded Redis socket timeouts (`0.5` seconds each) can create short false negatives under heavy latency, but this is aligned with fail-open and prevents request pileups.
- If `starlette` middleware ordering changes in future versions, the stack-wrapping assumptions could break, so stack assertions should be kept with tolerant class-order checks.
- Wrong middleware constructor args in `api/main.py` will now fail the new wiring test, which is intended to catch silent breakage early.
- `X-Request-ID` on `OPTIONS` depends on request-ID middleware being outer than CORS.

### Edge cases
- Missing `request.client` → use `ip:unknown` and still enforce safely.
- Invalid, missing, expired, or undecodable Bearer token → IP limit only.
- Request with no Redis reachable and slow network path → timeout quickly via configured socket settings, warning is logged, request is accepted.
- Authenticated and unauthenticated users behind one NAT share IP budget while users remain separately limited.
- Both IP and user keys exceed in one request → first detected limit short-circuits to one 429.
- `Retry-After` is always `60`, never derived from remaining-count math.

