# Solution plan

**Issue:** Add rate limiting per IP address in addition to per user — https://github.com/jamjamgobambam/pathreview/issues/70

### Understand

**Root cause.** The `RateLimiter` in [safety/rate_limiter.py](safety/rate_limiter.py) is a
generic, rolling-window, Redis-backed limiter that accepts *any* identifier
(`check_rate_limit(identifier, limit, window_seconds)`). On the baseline (`main`)
it is never invoked anywhere in the request path — `git grep check_rate_limit`
returns only its own definition and the unit tests, no call sites under `api/`.
So no request is bounded, and in particular unauthenticated requests to public
endpoints can be sent without any limit.

**Expected vs. actual.**
- *Expected:* every request is capped per client IP as a secondary layer,
  regardless of whether it carries a user identity, using the existing
  rolling-window limiter.
- *Actual (baseline):* unauthenticated requests pass through unthrottled;
  65 requests to `GET /` all returned `200` and zero `429`s in reproduction.

### Map

Files/modules involved:

- [safety/rate_limiter.py](safety/rate_limiter.py) — existing limiter; reused as-is,
  keyed with an `ip:<addr>` identifier. No change expected unless a helper is needed.
- [api/middleware/rate_limit.py](api/middleware/rate_limit.py) — **new** middleware
  (`IPRateLimitMiddleware`) that extracts the client IP and calls the limiter per request.
- [api/main.py](api/main.py) — register the middleware in the app's middleware stack.
- [core/config.py](core/config.py) — reuse `rate_limit_per_minute` (default 60) for the
  per-IP limit.
- `tests/` — a test verifying unauthenticated requests are throttled per IP.

### Plan

1. **Add `IPRateLimitMiddleware`** in [api/middleware/rate_limit.py](api/middleware/rate_limit.py):
   a Starlette `BaseHTTPMiddleware` that reads `request.client.host`, calls
   `RateLimiter.check_rate_limit("ip:<host>", limit, window_seconds)`, and returns
   `429` when the limit is exceeded.
2. **Wire it into the app** in [api/main.py](api/main.py) via `app.add_middleware(...)`,
   as a secondary layer that runs regardless of authentication state.
3. **Surface limiter state to clients** by setting an `X-RateLimit-Remaining` header on
   allowed responses, so callers can see how close they are to the cap.
4. **Add a test** that sends more than `limit` unauthenticated requests from one client
   and asserts a `429` appears, and that a different IP is unaffected.

### Inputs & outputs

- **Input:** each incoming HTTP request; the client IP (`request.client.host`), the
  configured per-minute limit, and the window.
- **Output / change:** requests over the per-IP cap receive `429` with a JSON
  `{"detail": ...}` body; allowed requests carry an `X-RateLimit-Remaining` header.
  No change to response bodies of allowed requests otherwise.

### Risks & unknowns

- **Client IP behind a proxy.** `request.client.host` is the socket peer; behind a
  reverse proxy/load balancer this may be the proxy IP, collapsing all clients into one
  bucket. Need to decide whether to trust `X-Forwarded-For` (and only from trusted hops).
- **Redis availability.** [safety/rate_limiter.py](safety/rate_limiter.py) *fails open* on
  Redis errors (returns allowed). Middleware creating its own client via
  `redis.Redis.from_url(settings.redis_url)` means a Redis outage silently disables
  per-IP limiting — acceptable for availability but worth calling out.
- **Middleware ordering.** Where `IPRateLimitMiddleware` sits relative to CORS / request-ID
  middleware in [api/main.py](api/main.py) affects whether rejected requests get CORS headers
  and request IDs.
- **Health-check traffic.** Aggressively limiting `GET /health` could cause orchestrators to
  mark the service unhealthy; may need to exempt health endpoints.

### Edge cases

- Missing client info: `request.client` is `None` → fall back to a sentinel like
  `"unknown"` rather than crashing.
- Two clients on the same NAT/proxy IP sharing a bucket (documented limitation).
- Redis unreachable → fail open, request allowed.
- Burst exactly at the boundary (`limit` allowed, `limit + 1` denied) — verified in
  reproduction with `limit=5`, denied at request #6.
- Rolling window: requests should be allowed again once older entries age out of the window.
