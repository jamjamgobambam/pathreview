## Solution plan

**Issue:** Add an API rate limiting header (`X-RateLimit-Remaining`) to responses —
https://github.com/ascherj/pathreview/issues/86

### Understand

**Expected behavior:** Every API response should carry `X-RateLimit-Limit` and
`X-RateLimit-Remaining` headers, so clients can see how much quota they have left
and back off proactively, instead of only discovering they've been throttled when
a request suddenly returns 429.

**Actual behavior (root cause):** `safety/rate_limiter.py` already contains a fully
implemented, fully unit-tested `RateLimiter` class with a
`check_rate_limit(identifier, limit, window_seconds=60) -> (allowed, remaining)`
method that does the actual rolling-window logic against Redis (sorted sets, `zadd`/
`zcard`/`zremrangebyscore`). The root cause is that **nothing in the API layer ever
calls it.** There's no middleware and no route dependency invoking `RateLimiter`, so:
- No response ever includes `X-RateLimit-Limit` / `X-RateLimit-Remaining`.
- No request is ever actually blocked with a 429, regardless of volume.

This was confirmed by reproduction: see `tests/manual/repro_issue_86.py`, run
against `main` — 5 requests to `GET /` all return `status=200` with both headers
`None`.

### Map

Files involved:
- `safety/rate_limiter.py` — existing `RateLimiter` class, reused as-is (no changes
  needed here; it already returns exactly what's needed).
- `api/middleware/request_id.py` — existing middleware used as the structural
  pattern to follow (`BaseHTTPMiddleware`, mutates `response.headers` before
  returning).
- `api/middleware/rate_limit.py` — **new file**, the middleware that wires
  `RateLimiter` into every request.
- `api/main.py` — needs `app.add_middleware(RateLimitMiddleware, ...)` registered,
  with attention to middleware ordering (Starlette applies middleware in reverse
  registration order — last added runs outermost).
- `core/config.py` — already has `redis_url` and `rate_limit_per_minute` settings
  defined; reused, not modified.
- `tests/unit/test_rate_limit_middleware.py` — **new file**, unit tests for the
  middleware following the `Mock()`-based Redis pattern already used in
  `tests/unit/test_rate_limiter.py`.

### Plan

1. **Reproduce the gap** (this week): confirm via a standalone script
   (`tests/manual/repro_issue_86.py`) that on `main`, no response carries rate-limit
   headers and nothing is ever blocked, regardless of request volume.
2. **Build `RateLimitMiddleware`** in `api/middleware/rate_limit.py`, following
   `RequestIDMiddleware`'s structure: construct a `RateLimiter` from a Redis client
   built off `settings.redis_url`, call `check_rate_limit()` once per request keyed
   on `request.client.host` (client IP — auth in this codebase is dependency-injected
   via `Depends(get_current_user)`, not middleware, so no authenticated user is
   available at the middleware layer).
3. **Handle both response paths**: if `allowed` is `False`, short-circuit and return
   a 429 directly (skip `call_next`); if `True`, call `call_next()` as normal. In
   *both* cases, set `X-RateLimit-Limit` and `X-RateLimit-Remaining` on the response
   before returning it, so the headers are present even on the 429 path.
4. **Register the middleware** in `api/main.py`, ordered so `RequestIDMiddleware`
   stays outermost (for log correlation on every response, including 429s) and
   `RateLimitMiddleware` wraps route handling.
5. **Add unit tests** mirroring `tests/unit/test_rate_limiter.py`'s mock-Redis
   fixture style: headers present on success, headers correct when near/at the
   limit, 429 + `X-RateLimit-Remaining: 0` when exceeded, remaining never negative.

### Inputs & outputs

- **Input:** every incoming HTTP request to the FastAPI app; the client's IP
  (`request.client.host`) as the rate-limit identifier; `settings.rate_limit_per_minute`
  as the limit.
- **Output:** every response (success or error) gains two headers,
  `X-RateLimit-Limit` (constant, from config) and `X-RateLimit-Remaining` (computed
  per-request from `RateLimiter.check_rate_limit`). Requests beyond the limit get a
  `429` response instead of reaching the route handler.

### Risks & unknowns

- **No shared Redis client factory exists yet** — `RateLimiter`, `safety/monitoring.py`,
  and `agent/memory/session_store.py` each take a `redis_client` via constructor
  injection with no common source. Building the client inline in the middleware
  (`redis.from_url(settings.redis_url)`) is the smallest fix, but means the
  middleware owns its own Redis connection rather than sharing a pool — worth
  revisiting if a shared factory gets introduced later.
- **Sync vs async Redis:** `RateLimiter.check_rate_limit` calls the Redis client
  synchronously (no `await`). Must keep using sync `redis.Redis` / `redis.from_url`,
  not `redis.asyncio`, or the middleware will break silently on the client calls.
- **Fail-open behavior:** `RateLimiter.check_rate_limit` already catches Redis
  connection errors and fails open (`return True, limit`) — confirmed during
  reproduction testing (local Redis absent, requests still succeeded with
  `X-RateLimit-Remaining: 60`). This is inherited behavior, not something this
  fix changes, but it's worth being explicit that a Redis outage means rate
  limiting silently stops enforcing rather than blocking all traffic.
- **IP-based keying is coarse:** because `BaseHTTPMiddleware` runs before route
  dependencies resolve, there's no access to the authenticated user, so all
  unauthenticated clients behind the same NAT/proxy share one bucket. Keying on
  user id instead would require moving rate limiting into a route dependency
  (bigger change) — out of scope for this issue but worth flagging.
- **Middleware ordering is easy to get backwards** — Starlette's reverse
  registration-order semantics for `add_middleware` are non-obvious; verified by
  reproduction that `X-Request-ID` still appears on 429 responses with the chosen
  ordering.

### Edge cases

- Redis unreachable → fails open (allowed, `remaining=limit`), confirmed by
  reproduction; logged as `rate_limiter_error` via existing logging in
  `RateLimiter`.
- `request.client` is `None` (e.g. some test clients / edge transports) → identifier
  falls back to `"unknown"`, all such requests share one bucket rather than crashing.
- Request lands exactly at the limit boundary → `remaining` must never go negative
  (`max(remaining, 0)` on the header value), and the boundary request itself should
  still be `allowed=True` per `RateLimiter`'s existing `current_count < limit` check.
- 429 response must still carry both headers (not just success responses) — a
  client parsing headers shouldn't need to branch on status code to find its quota.
- Very first request from a brand-new identifier (empty Redis key) → `zcard` returns
  0, should be allowed with `remaining = limit - 1`, already covered by
  `RateLimiter`'s existing unit tests.
