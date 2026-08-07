## Solution plan

**Issue:** [Add an API rate limiting header (`X-RateLimit-Remaining`) to responses](https://github.com/ascherj/pathreview/issues/86
)

### Understand

Currently, there is no way for API clients to know their request limit or remaining requests before being blocked from the service with a 429 error. This improvement adds two headers to every HTTP response: `X-RateLimit-Limit` and `X-RateLimit-Remaining`. The proposed solution adds middleware that attaches these two headers to each client request response. There is no existing functionality that attaches the appropriate headers to responses, but there is a function that checks if a client request is within the rate limit.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

Files I plan to touch:
- Add a new `rate_limit.py` middleware file to `api/middleware` which calls `safety/rate_limiter.py`. 
- Add the newly created middleware to `main.py`. 
- Add integration tests (to newly created `tests/integration/test_rate_limit_headers.py`).

Files involved:
- Existing rate limit is defined by `rate_limit_per_minute` in `config.py` and is set to `60`.
- Token decode logic in `core/security.py`.

### Plan

1. Read `core/security.py` and confirm `decode_access_token()`'s exact signature: what it returns on success, and what it raises on an invalid/expired token. Confirm what `create_access_token` sets to the user's ID.
2. Read `api/middleware/request_id.py` as the template for the new middleware and confirm the `BaseHTTPMiddleware` and `dispatch(request, call_next)` shape. Read `api/main.py` to see how middleware is added to the api.
3. Read `safety/rate_limiter.py` in full and confirm `check_rate_limit(identifier, limit, window_seconds)`'s exact return shape and whether `limit` needs to be passed in or is read internally.
4. Create `api/middleware/rate_limit.py` with a `RateLimitMiddleware(BaseHTTPMiddleware)`:
   - In `dispatch()`, resolve the identifier: check `request.headers.get("Authorization")` for a `Bearer` token. Ff present and decodable, use the `sub` claim. Otherwise fall back to IP address.
   - Call `check_rate_limit()`.
   - If not allowed, construct and return a 429 response with `X-RateLimit-Limit` and `X-RateLimit-Remaining` attached.
   - If allowed, it calls `call_next(request)` to run the endpoint, attaches both headers, the returns the response.
5. Add `RateLimitMiddleware` to `main.py`.
6. Run `make test-unit` to confirm nothing existing breaks before wiring this in further.
7. Update `tests/integration/test_rate_limit_headers.py` with additional tests.
8. Run `make test-integration` to confirm the new tests pass.
9. Run `make check` to verify lint, formatting, and types are clean.

### Inputs & outputs

**Middelware I'm Adding:** `RateLimitMiddleware` (extends `BaseHTTPMiddleware` class) with the function `dispatch()` which takes `request` (a request) and `call_next` (fuction) as inputs. Calls `safety/rate_limiter.check_rate_limit()` and receives `(allowed, remaining)`. Either runs the endpoint if allowed (attaching the rate limit headers and returns the resposne) or constructs a 429 response with rate limit headers and returns it. 

**New Behavior:**
- `main.py` adds new `RateLimitMiddleware` to the api.
- Every request includes `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers, including 429 responses. 

### Risks & unknowns

- I'm unsure if the order in which the middleware is registered is critical.
- I'm opting not to exclude the system health checks (those that hit the `/health` endpoint), assuming that system health checks are not likely to exceed 60 / minute. That said, if the configured rate limit is lowered, this could be a future issue.
- Redis is new to me, so I need to research it further to understand some of the methods used in `safety/rate_limiter.py`. 

### Edge cases

1. An `Authorization` header that's present but doesn't decode (garbage token, expired token, missing `sub` claim) should fall back to the IP identifier rather than raising an unhandled exception.
2. Falling back to IP assumes `request.client.host` exists. The solution needs to guard against `request.client` itself being `None` so the middleware doesn't crash.