## Solution plan

**Issue:** [#86 — Add an API rate limiting header (`X-RateLimit-Remaining`) to responses](https://github.com/ascherj/pathreview/issues/86)

### Understand

What should happen: every response carries `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers so a client can see it's getting close to the limit and back off on its own, and going over the limit should get a real 429.

What actually happens: nothing. No headers, no 429, ever. I confirmed this by running the app locally and hitting the root endpoint, `curl -i http://localhost:8000/` comes back with `x-request-id` (because `RequestIDMiddleware` is registered) but nothing rate-limit related at all.

### Map

- `api/main.py`: this is where `RequestIDMiddleware` and `CORSMiddleware` get registered with `app.add_middleware(...)`. The new rate limit middleware needs to go here too.
- `api/middleware/request_id.py`: basically the template for what I'm building. Same `BaseHTTPMiddleware` + `dispatch` shape, same "stamp a header on the way out" pattern.
- `safety/rate_limiter.py`: reusing `RateLimiter` as-is, don't think it needs changes.
- `core/config.py`: already has `rate_limit_per_minute` (defaults to 60), so I should pull the limit from there instead of hardcoding it.
- New file: `api/middleware/rate_limit.py` — where the actual middleware lives.
- Need a Redis client to hand to `RateLimiter(redis_client)`. `api/routes/health.py` builds one inline for its health check. I'll probably follow that same pattern rather than invent a new one, unless it turns out there's a cleaner shared spot for it.
- `tests/`: will add a test or two around the middleware itself.

### Plan

1. Get a Redis client available to the middleware, built from the same `redis_url`/`redis_host`/`redis_port` settings `health.py` already uses.
2. Write `RateLimitMiddleware` in `api/middleware/rate_limit.py`, on `dispatch`, figure out an identifier (authenticated user id if there's a valid token, otherwise IP), call `RateLimiter.check_rate_limit`, and either let it through or bail out with a 429.
3. Stamp `X-RateLimit-Limit` / `X-RateLimit-Remaining` on the response either way — allowed or denied — same idea as how `X-Request-ID` gets added in `request_id.py`.
4. Wire it into `api/main.py` with `app.add_middleware(...)`. Need to think about ordering relative to the other middleware — probably wants to run early, but after request ID so a 429 still gets a request id attached to it.
5. Add tests: something unit-level for the identifier picking / header stamping logic, and something that actually hits a route through `TestClient` and checks the headers show up and a 429 shows up once you go over.

### Inputs & outputs

Input is every incoming request, identified by user id if it's authenticated, otherwise by IP (since stuff like `/auth/login` and `/auth/register` are hit before anyone has a token).

Output is `X-RateLimit-Limit` and `X-RateLimit-Remaining` on every response, plus a 429 instead of the normal response once someone's over their limit (still with those headers attached, `remaining` just reads 0).

### Risks & unknowns

- There's no shared Redis client anywhere right now, `health.py` just builds its own inline. I don't want to create a new Redis connection per request, so I need to figure out where a single client instance should actually live.
- `RateLimiter` uses the plain sync `redis` client, but literally everything else in this app is async. Calling a blocking Redis call inside an async `dispatch` could stall the event loop under real load. Not sure yet if that's in scope for this fix or something to flag and leave alone — need to look closer once I'm actually in the code.
- IP-based limiting for unauthenticated routes assumes I can reliably get the caller's IP, but nothing in the codebase handles `X-Forwarded-For` / proxies today. Probably out of scope, but worth calling out so it doesn't get treated as "done."
- Not sure `/health` should count against anyone's limit at all — might need to exclude specific paths from the middleware entirely.
- `check_rate_limit` fails open on Redis errors (returns allowed + full limit as remaining), which is reasonable, but I need to make sure the middleware doesn't report a misleading `X-RateLimit-Remaining` in that situation.

### Edge cases

- No auth token AND no clean way to get an IP (e.g. running under `TestClient` in tests), the identifier fallback still needs to produce something stable.
- Redis is down,  shouldn't take the whole app down with it, should fail open the same way `RateLimiter` already does.
- Exactly at the limit vs. one over it — needs to match the off-by-one behavior `RateLimiter` already has (`remaining = limit - current_count - 1`), which the existing unit tests already pin down.
- A few requests from the same identifier landing back-to-back, `check_rate_limit` isn't atomic (it's `zremrangebyscore` + `zcard` + `zadd` as three separate Redis calls), so there's a small race window. Probably fine for this scope, but worth a note rather than pretending it's not there.
- Paths that probably shouldn't be rate-limited at all like health checks, docs/OpenAPI routes.
