## Solution plan

**Issue:** [#86 — Add an API rate limiting header (X-RateLimit-Remaining) to responses](https://github.com/ascherj/pathreview/issues/86)

### Understand

The `RateLimiter` class in `safety/rate_limiter.py` already implements a working rolling-window limiter against Redis and its `check_rate_limit()` method returns a `(allowed: bool, remaining: int)` tuple — so the two values the issue asks us to expose on responses (the configured limit and the remaining count) are already computed. What is missing is that **no code in the API layer ever calls `check_rate_limit()`**. `grep -rn RateLimiter api/` returns no matches, and `api/main.py:44-54` only registers `CORSMiddleware` and `RequestIDMiddleware`. Because of this, two things are broken today: (a) no `X-RateLimit-Limit` / `X-RateLimit-Remaining` header is attached to any response, and (b) no request is ever throttled — my reproduction showed 100 consecutive requests to `/` all returning `200`.

Expected behavior after the fix: every response (both `200`s and `429`s) carries `X-RateLimit-Limit: <configured_limit>` and `X-RateLimit-Remaining: <remaining>`. When the limiter reports `allowed=False`, the middleware short-circuits with a `429 Too Many Requests`, still carrying those two headers plus `Retry-After`, without ever invoking the downstream route.

**Root cause:** The `RateLimiter` class is not registered as FastAPI middleware. The fix is a new middleware that wraps every request, calls the existing limiter, and attaches the headers.

### Map

Files I expect to touch:

- `api/middleware/rate_limit.py` — **new file.** A `BaseHTTPMiddleware` subclass modeled on `api/middleware/request_id.py:10-34`. Instantiated with a `RateLimiter` and a per-minute limit. Sets the two headers on every response and returns `429` when the limiter rejects.
- `api/main.py:44-54` — where middleware is registered. I'll construct a `redis.Redis` client from `settings.redis_url` on startup, build a `RateLimiter`, and `app.add_middleware(RateLimitMiddleware, ...)` after the `RequestIDMiddleware` line (so the request_id contextvar is bound before the rate-limit code logs anything).
- `safety/rate_limiter.py:21-63` — **read only.** `check_rate_limit(identifier, limit, window_seconds)` returns `(allowed, remaining)`. I do not need to change this.
- `core/config.py:12,40` — `redis_url` and `rate_limit_per_minute: int = Field(default=60)` already exist. No config change needed.
- `api/routes/health.py:44` — only existing site that constructs a `redis.Redis` client. I'll follow the same construction pattern (host/port from `settings.redis_url`) so the middleware behaves consistently.
- `tests/integration/test_rate_limit_headers.py` — **new file.** The `tests/integration/` directory currently only has `__init__.py`, so this will be the first integration test. It will use FastAPI's `TestClient` against `api.main:app` with a fake Redis (either `fakeredis` or a mock passed into the middleware).
- `docs/JOURNAL.md` — Week 9 entry noting the implementation.

### Plan

1. **Confirm the Redis client shape.** ✅ **Done.** Investigating `api/routes/health.py:44-49` revealed a latent bug — it constructs the client with `settings.redis_host` / `settings.redis_port`, but neither field exists in `core/config.py` (only `redis_url` does), and `.env` / `.env.example` don't set them either. The `AttributeError` is silently swallowed by the surrounding `try/except`, which is why my reproduction's `/health` reported `redis: "unhealthy"` even though Redis is running locally. **I will NOT copy this pattern.** Instead use `redis.Redis.from_url(settings.redis_url, decode_responses=True)` — the field that actually exists and is populated by `.env`. Verified in a REPL: redis-py 8.0.1 exposes `from_url()` and it returns a `Redis` instance. The client will be constructed **once** at app startup in `api/main.py` (a fresh `redis.Redis(...)` per request would allocate a new connection pool). The `health.py` bug is out of scope for this PR — I'll note it in the PR description as a suggested follow-up.
2. **Create `api/middleware/rate_limit.py`.** A `RateLimitMiddleware(BaseHTTPMiddleware)` with `__init__(self, app, limiter: RateLimiter, limit: int, window_seconds: int = 60)`. The `dispatch()` method:
   - Derives an `identifier` — user id if `request.state` has one from a prior auth step, else `request.client.host` for anonymous callers, else the literal string `"unknown"` for the edge case where `request.client` is `None` (test clients).
   - Calls `limiter.check_rate_limit(identifier, limit, window_seconds)`.
   - If `allowed is False`: return `JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}, headers={"X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0", "Retry-After": str(window_seconds)})`.
   - If `allowed is True`: `response = await call_next(request)`, then set `response.headers["X-RateLimit-Limit"] = str(limit)` and `response.headers["X-RateLimit-Remaining"] = str(remaining)`, then return.
3. **Wire it in `api/main.py`.** After the `RequestIDMiddleware` line, construct the Redis client, build `RateLimiter(redis_client)`, and register `app.add_middleware(RateLimitMiddleware, limiter=limiter, limit=settings.rate_limit_per_minute, window_seconds=60)`.
4. **Re-run the reproduction.** `curl -si http://localhost:8000/ | head -20` — headers should now include `X-RateLimit-Limit: 60` and `X-RateLimit-Remaining: 59` on the first request, decrementing on subsequent ones. `for i in $(seq 1 70); do ... done | sort | uniq -c` — the last ~10 requests should now return `429`.
5. **Write the integration test.** Instantiate the app with a `fakeredis.FakeRedis` client so the test is hermetic. Assert (a) `X-RateLimit-Limit` and `X-RateLimit-Remaining` are present on a `200` response, (b) `X-RateLimit-Remaining` decrements across two calls, (c) after exceeding the limit, the response is `429` with `Retry-After` and the same two headers.
6. **Run `make test-unit` and `make test-integration`** (or whatever the Makefile provides) to confirm no regressions.
7. **Run `make check`** (lint/format/type checks) if that target exists.
8. **Update `docs/JOURNAL.md` Week 9** with a link to the fix commit and the fresh curl output showing the headers.

### Inputs & outputs

**New class:** `api.middleware.rate_limit.RateLimitMiddleware(BaseHTTPMiddleware)`

**Constructor:** `__init__(self, app, limiter: RateLimiter, limit: int, window_seconds: int = 60)`

**`dispatch(request, call_next) -> Response` contract:**

| Case | Return | Headers set on response |
| --- | --- | --- |
| First request from identifier | `200` (or downstream status) | `X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 59` |
| Nth request, still under limit | downstream status | `X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 60 - N` |
| Limit exceeded | `429` (short-circuit, does NOT call `call_next`) | `X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 0`, `Retry-After: 60` |
| Redis error | downstream status (fail open — `RateLimiter` already does this at `safety/rate_limiter.py:60-63`) | Headers omitted, request proceeds |

**Existing signatures I am NOT changing:** `RateLimiter.__init__`, `RateLimiter.check_rate_limit`, and every route handler. This is purely additive at the middleware layer.

**Test drafted in advance:**

```python
# tests/integration/test_rate_limit_headers.py
def test_ratelimit_headers_present_on_200(client_with_fake_redis):
    resp = client_with_fake_redis.get("/")
    assert resp.status_code == 200
    assert resp.headers["X-RateLimit-Limit"] == "60"
    assert resp.headers["X-RateLimit-Remaining"] == "59"

def test_ratelimit_remaining_decrements(client_with_fake_redis):
    r1 = client_with_fake_redis.get("/")
    r2 = client_with_fake_redis.get("/")
    assert int(r2.headers["X-RateLimit-Remaining"]) == int(r1.headers["X-RateLimit-Remaining"]) - 1

def test_ratelimit_returns_429_when_exceeded(client_with_low_limit):
    for _ in range(5):
        client_with_low_limit.get("/")
    resp = client_with_low_limit.get("/")  # 6th call, limit=5
    assert resp.status_code == 429
    assert resp.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in resp.headers
```

### Risks & unknowns

1. **Sync `redis.Redis` inside an async middleware will block the event loop.** `safety/rate_limiter.py:3` uses the sync client, and `agent/memory/session_store.py:14` / `market_analyzer.py:41` do too — the whole codebase is on sync Redis. Calls to `zremrangebyscore` + `zcard` + `zadd` per request are cheap (single-digit ms locally) but this is a real trade-off. **Decision I need to make:** stick with sync for consistency, or migrate to `redis.asyncio` (bigger change, out of scope for this fix). Current plan: stick with sync, note the follow-up in the PR description.
2. **Identifier strategy for unauthenticated routes.** `/`, `/health`, `/auth/login`, and `/auth/register` don't have a user id yet. Falling back to `request.client.host` is standard, but behind a reverse proxy that IP will be the proxy's — I'll need to check whether the app has an `X-Forwarded-For` config. **Investigation:** grep for `forwarded` / `trust_proxy` in `api/main.py` and `core/config.py`. If missing, I'll use `request.client.host` and flag proxy-awareness as a follow-up.
3. **Middleware ordering.** Starlette applies middleware in reverse-added order for the request path. `RequestIDMiddleware` is currently the last thing added, so it runs first. If I add rate-limit after it, rate-limit runs first — before the request_id is bound to structlog — meaning rate-limit log lines won't carry the request_id. **Decision:** add rate-limit *before* `RequestIDMiddleware` in the source (so RequestID runs first at request time and rate-limit logs carry the id). Verify with a real log line during step 4 of the plan.
4. **`/health` exemption.** Load balancers hammer `/health`; if it counts against the limit, a single LB IP will trip the limiter constantly. **Decision:** exempt `/health` (and probably `/`) by early-returning from `dispatch` if `request.url.path in {"/health", "/"}`. Confirm with maintainer expectation in the PR.
5. **What does `check_rate_limit` return when Redis is down?** Reading `safety/rate_limiter.py:60-63`, it returns `(True, limit)` — fail open. In that path my middleware will happily set `X-RateLimit-Remaining: 60` on every response, which lies to clients. **Decision:** when the limiter returns exactly `(True, limit)` after a Redis error, omit the headers rather than emit misleading values. But that means I can't distinguish "Redis is down" from "this is the first request." **Investigation:** consider adding a return-code or exception path from `RateLimiter` to distinguish the two, or accept the small lie as the cost of fail-open.

### Edge cases

- **Anonymous request (no user id):** identifier falls back to `request.client.host`. Middleware still sets both headers.
- **Test client with `request.client is None`:** identifier falls back to the string `"unknown"`. Middleware still sets headers — this keeps the integration test path clean.
- **Two clients sharing an IP (NAT):** they will share a bucket. Documented limitation, not a bug for this fix.
- **Exactly-at-limit request:** the Nth call where N = limit should still succeed with `X-RateLimit-Remaining: 0`. The N+1th should be `429`. This matches `safety/rate_limiter.py:44-52` (adds the entry only if `current_count < limit`).
- **429 response body:** must be JSON with a `detail` field, matching the app's existing error shape (see `api/main.py:69-75` for the generic 500 pattern).
- **CORS preflight `OPTIONS`:** CORS middleware handles these before mine — since `CORSMiddleware` is added first (line 45) and runs last on the response, my middleware will still see the `OPTIONS` request. **Open question:** should preflights count against the limit? Probably not. Add `if request.method == "OPTIONS": return await call_next(request)` if it becomes an issue.
- **Redis outage mid-window:** limiter fails open per `safety/rate_limiter.py:62-63`. Middleware must not crash; must not lie in headers (see risk #5).
