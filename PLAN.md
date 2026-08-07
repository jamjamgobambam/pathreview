## Solution plan

**Issue:** [Add an API rate limiting header (X-RateLimit-Remaining) to responses #86](https://github.com/ascherj/pathreview/issues/86)

### Understand
The current behaviour:
- safety/rate_limiter.py calculates the count of requests left until the limit is reached and correctly returns True or False along with the remaining count of requests.
- No middleware exists to throw an error or include headers containing the request count information.

The expected behavior:
- **Allowed (`True`) case:** let the request proceed and attach `X-RateLimit-Limit` and
  `X-RateLimit-Remaining` headers to the outgoing response.
- **Denied (`False`) case:** throw a 429 response stating the request limit has been exceeded.

**Root cause:** There is no wiring between `RateLimiter.check_rate_limit()` and the FastAPI
request/response cycle and the headers have not been created yet.

### Map
Files I expect to touch:
- `api/middleware/rate_limit.py` — **new file.** A `BaseHTTPMiddleware` subclass following the
  structure of `RequestIDMiddleware` in `request_id.py` (line 10): override `dispatch()`, call
  `check_rate_limit()` before/after `call_next()`, and set headers on the `Response`.
- `api/main.py` — register the new middleware with `app.add_middleware(...)` next to the
  existing `app.add_middleware(RequestIDMiddleware)` (line 54), and add the import at the top
  (line 7).
- `tests/unit/test_rate_limit_header.py` — Unit test asserting the headers appear on an allowed 
  response and that a 429 is returned once the limit is exceeded.

Files I need to read but likely won't change:
- `safety/rate_limiter.py` — `check_rate_limit()` is the function being called.
- `api/middleware/auth.py` — reference for how a 401 `HTTPException` is raised with headers
  (line 27). I will follow this strucutre.

### Plan
1. Create `api/middleware/rate_limit.py` with a `RateLimitMiddleware(BaseHTTPMiddleware)`:
   - In `dispatch()`, resolve the identifier, then call `check_rate_limit(identifier, limit)`.
   - If `allowed` is `False`, return a `JSONResponse` with status 429 and the rate-limit headers,
     without calling `call_next()`.
   - If `allowed` is `True`, `response = await call_next(request)`, then set
     `response.headers["X-RateLimit-Limit"]` and `["X-RateLimit-Remaining"]` before returning.
2. Register the middleware in `api/main.py`.
3. Write `tests/integration/test_rate_limit_header.py`.
4. Run `make test-integration` again to confirm the new test passes.

**Integration Test:**

```python
def test_response_includes_rate_limit_headers(client):
    """An allowed request should return X-RateLimit-Limit and X-RateLimit-Remaining."""
    response = client.get("/")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers


def test_exceeding_limit_returns_429(client):
    """Once the limit is exceeded, the API should return 429."""
    # send more than `limit` requests within the window
    ...
    assert response.status_code == 429
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
```

### Risks & unknowns
1. **`check_rate_limit` fails open on Redis errors** (returns `True, limit`). That's the existing
   design, so my middleware should treat that as "allowed" and still set headers — I'll make sure
   I don't crash when `remaining == limit`.
2. **Where `limit` and `window_seconds` come from.** If they aren't already configured, I'll pull
   them from settings/env with sensible defaults rather than hard-coding them in the middleware.
