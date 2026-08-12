## Solution plan

**Issue:** #70 — Add rate limiting per IP address in addition to per user
https://github.com/ascherj/pathreview/issues/70

### Understand
The issue's premise is that per-user rate limiting already exists and only per-IP is
missing. That's not what I found when I reproduced it (see JOURNAL.md, Week 8): `RateLimiter`
in `safety/rate_limiter.py` is a fully working, unit-tested class, but nothing calls
`check_rate_limit()` anywhere in the app. There's no `RateLimitMiddleware`, and no route
depends on one. `api/main.py` registers `CORSMiddleware` and `RequestIDMiddleware` but no
rate limiter. So the real root cause is broader than the issue title states: **no request,
authenticated or not, is throttled at all today.**

Expected behavior: every request should be checked against an IP-based limit (since IP is
the only thing we always have, even for anonymous traffic), and requests carrying a valid
JWT should *additionally* be checked against a per-user limit, so one heavy user can't
exhaust the whole IP bucket for everyone behind a shared NAT/proxy, and one abusive
anonymous client can't hide behind "no auth = no limit."

**Root cause:** `RateLimiter` exists but was never wired into the request path — no
middleware/dependency calls it.

### Map
Files I expect to touch:
- `api/middleware/rate_limit.py` (new) — `RateLimitMiddleware(BaseHTTPMiddleware)`. Modeled
  on the existing `api/middleware/request_id.py` (same `BaseHTTPMiddleware` + `dispatch()`
  pattern), since this has to run for *every* request including ones with no auth
  dependency, so it can't be a per-route `Depends`.
- `api/main.py` (lines 44-54) — register the new middleware. Ordering matters: Starlette
  runs the *last*-added middleware outermost (first on the request, last on the response).
  Currently: `CORSMiddleware` added first, `RequestIDMiddleware` added second (outermost).
  I need `RequestIDMiddleware` to still run before rate limiting (so `request.state.request_id`
  exists for logging), and `CORSMiddleware` to wrap the rate limiter (so a `429` still gets
  CORS headers for browser clients). That means `RateLimitMiddleware` must be added
  **first** — before `CORSMiddleware` — so the final add order is:
  `RateLimitMiddleware` → `CORSMiddleware` → `RequestIDMiddleware`.
- `core/config.py` — no new fields needed; reuse the existing `rate_limit_per_minute`
  (line 40) for both layers rather than adding new settings the issue didn't ask for.
- `safety/rate_limiter.py` — no changes; `check_rate_limit(identifier, limit, window_seconds)`
  already accepts any string identifier, so I'll just call it twice with different prefixes
  (`ip:<addr>` / `user:<id>`).
- `core/security.py` — reuse `decode_access_token()` (line 69) to read the JWT `sub` claim
  for the user-layer key. I will **not** duplicate `get_current_user`'s DB lookup here (see
  Risks below).
- `tests/integration/test_rate_limiting_reproduction.py` — already added in Week 8 as the
  reproduction. It should flip from failing to passing once this lands, plus I'll add
  focused unit tests for the new middleware.
- `tests/unit/test_rate_limit_middleware.py` (new) — unit tests for the middleware in
  isolation, mocking `RateLimiter.check_rate_limit`.

### Plan
1. Instantiate a module-level `redis.Redis.from_url(settings.redis_url)` client and a
   `RateLimiter` wrapping it inside `api/middleware/rate_limit.py` (mirrors how `health.py`
   builds a Redis client — except using `from_url`, since `settings.redis_host`/`redis_port`
   don't actually exist on `Settings`, only `redis_url` does).
2. Implement `RateLimitMiddleware.dispatch()`:
   - Resolve the client IP from `request.client.host` (fall back to `"unknown"` if `request.client`
     is `None`, e.g. some ASGI test transports).
   - Call `check_rate_limit(f"ip:{ip}", limit=settings.rate_limit_per_minute)`. If not
     allowed, short-circuit and return a `429 JSONResponse` immediately (skip the user check
     — no point spending a second Redis round trip on a request we're already blocking).
   - If the request has an `Authorization: Bearer <token>` header, try
     `decode_access_token(token)`; on success, pull `payload["sub"]` and call
     `check_rate_limit(f"user:{sub}", limit=settings.rate_limit_per_minute)`. Wrap the decode
     in try/except — a malformed/expired token here just means "treat as anonymous for
     rate-limiting purposes," since `get_current_user` is still the real auth gate downstream.
   - Otherwise call `call_next(request)` and return its response.
3. Wire it into `api/main.py` in the order described in Map, before `CORSMiddleware`.
4. Write `tests/unit/test_rate_limit_middleware.py`: mock `RateLimiter.check_rate_limit` to
   return `(False, 0)` for the IP key and assert a `429` with no downstream call; mock it to
   allow the IP but deny the user key and assert the same; mock both allowed and assert the
   wrapped route actually runs.
5. Run `tests/integration/test_rate_limiting_reproduction.py` and confirm it now passes
   (429 shows up once the per-minute IP limit is exceeded).
6. Run the full unit suite (`pytest tests/unit -m unit`) to confirm nothing else regressed,
   then lint/type-check (`ruff check .`, `mypy .`).

### Inputs & outputs
**New class:** `RateLimitMiddleware(BaseHTTPMiddleware)` in `api/middleware/rate_limit.py`

**Existing happy path today:** every request reaches its route handler unconditionally.

**New behavior:**
- Input: any request, no `Authorization` header → checked only against `ip:<client_ip>`.
  Under the limit → passes through unchanged. Over the limit → `429` with
  `{"detail": "Rate limit exceeded", "request_id": ...}`, route handler never runs.
- Input: request with a valid `Authorization: Bearer <jwt>` → checked against both
  `ip:<client_ip>` and `user:<sub>`. Either one over its limit → `429`.
- Input: request with an invalid/expired `Authorization` header → checked only against
  `ip:<client_ip>` (falls back to anonymous bucketing); `get_current_user` still returns
  `401` later if the route requires auth.

**Test I'll write (unit, mocked Redis):**
```python
def test_ip_over_limit_returns_429_without_calling_route(monkeypatch):
    """RateLimitMiddleware should short-circuit with 429 when the IP bucket is full."""
    ...
    with patch.object(RateLimiter, "check_rate_limit", return_value=(False, 0)):
        response = client.get("/")
    assert response.status_code == 429
```

### Risks & unknowns
1. **Trusting `X-Forwarded-For` vs `request.client.host`.** If this API sits behind a load
   balancer/reverse proxy in production, `request.client.host` is the proxy's IP, not the
   real client's — every request would collapse into one IP bucket. The naive fix (reading
   `X-Forwarded-For`) is spoofable by any client unless there's a trusted-proxy allowlist,
   and I found no such config (`core/config.py` has no `trusted_proxies` setting). Given
   that, I'm deliberately using `request.client.host` only, and calling out in the PR that
   this is safe for the current deployment but will need a trusted-proxy config if this ever
   sits behind a proxy — not solving that here since it's outside this issue's scope.
2. **Per-user layer trusts the JWT signature only, not the DB.** Doing a full
   `get_current_user`-style DB lookup inside middleware means every request pays for two DB
   round trips (once in the middleware, once in the route's own `Depends`). I'm choosing to
   decode-and-trust the `sub` claim for bucketing purposes only; actual authorization is
   unaffected since `get_current_user` still runs downstream. Flagging this as a deliberate
   trade-off, not an oversight.
3. **Sync Redis client inside an async `dispatch()`.** `RateLimiter` (and the tests it
   already has) use the sync `redis.Redis` client, not `redis.asyncio`. Calling it inside
   `dispatch()` blocks the event loop for the duration of the Redis round trip. This matches
   the existing contract of `RateLimiter` (I'm not changing that class), but under heavy
   concurrent load this could become a bottleneck — noting it, not fixing it, since
   switching `RateLimiter` to async is a bigger change than this issue calls for.
4. **`settings.redis_host` / `settings.redis_port` don't exist.** I noticed `api/routes/health.py`
   (lines 44-46) already references those two fields, which aren't defined on `Settings` (only
   `redis_url` is) — that health check silently reports "unhealthy" via the broad `except`.
   That's a pre-existing, separate bug; I'm not touching `health.py`, just making sure my own
   code uses `redis.Redis.from_url(settings.redis_url)` instead of repeating that mistake.
5. **What counts as "the limit" for two layers?** Reusing one `rate_limit_per_minute` value
   for both IP and user layers keeps this change minimal, but it means a single authenticated
   user could still be capped by the shared IP bucket if many users share a NAT/proxy IP.
   Not adding a second config value now since the issue doesn't ask for independently tunable
   limits — flagging as a reasonable follow-up.

### Edge cases
- No `Authorization` header at all (public endpoint, e.g. `/health`, `/`): only the IP layer
  applies — this is the actual bug being fixed.
- Expired or tampered JWT: `decode_access_token` returns `None` / raises — treated as
  anonymous for rate-limiting, IP layer still applies, `get_current_user` still 401s
  downstream on protected routes.
- `request.client` is `None` (seen with some ASGI test transports): fall back to an
  `"unknown"` IP bucket rather than raising, so requests aren't accidentally exempted from
  all rate limiting.
- Redis unreachable: `RateLimiter.check_rate_limit` already fails open (returns
  `(True, limit)`) on any Redis exception — I'm relying on that existing behavior rather than
  adding a second failure-handling path in the middleware.
- Many users behind the same IP (office NAT, corporate VPN): they'll share one IP bucket in
  addition to their individual user buckets — expected given this design, called out in
  Risks above rather than solved here.
