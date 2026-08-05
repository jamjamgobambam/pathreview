## Solution plan

**Issue:** [Add integration tests for authentication edge cases #90](https://github.com/ascherj/pathreview/issues/90)

### Understand
The auth middleware in `api/middleware/auth.py` handles JWT validation via `get_current_user`, which calls `decode_access_token` from `core/security.py`. The existing test file (`tests/integration/test_auth_middleware.py`) only covers the happy path — a valid token with a real user. There are no tests for the four failure modes the middleware is supposed to handle: expired tokens, malformed tokens, missing Authorization header, and tokens signed with the wrong secret. A correct implementation would return HTTP 401 for all four of these cases.

### Map
Files involved:
- `tests/integration/test_auth_middleware.py` — the only file being created/modified
- `api/middleware/auth.py` — the middleware under test (`get_current_user` function)
- `core/security.py` — `create_access_token` and `decode_access_token` used to generate test tokens
- `core/config.py` — where `SECRET_KEY` and `jwt_algorithm` settings live
- `api/main.py` — the FastAPI app instance used to spin up the async test client

### Plan
1. Set up an async HTTP test client using `httpx.AsyncClient` with `ASGITransport` pointing at the FastAPI app — this lets tests make real requests without needing a running server.
2. Write a test for **expired tokens** by calling `create_access_token` with a negative `expires_delta`, then hitting a protected endpoint and asserting a 401 response.
3. Write a test for **malformed tokens** by sending a random garbage string as the Bearer token and asserting a 401 response.
4. Write a test for **missing Authorization header** by making a request to a protected endpoint with no headers and asserting a 401 response.
5. Write a test for **wrong-secret tokens** by using `jose.jwt.encode` directly with a hardcoded fake secret, sending that token, and asserting a 401 response.

### Inputs & outputs
- **Input:** HTTP requests to `GET /profiles/{profile_id}` (a protected route) with various malformed or missing auth headers
- **Output:** Each test asserts the response status code is `401 Unauthorized`
- **What changes:** One new file — `tests/integration/test_auth_middleware.py` — goes from not existing to containing 4 passing integration tests

### Risks & unknowns
- The app's lifespan startup in `api/main.py` connects to PostgreSQL on boot. The test client using `ASGITransport` may trigger the lifespan and fail if Docker isn't running — need to verify tests can run with the DB up, or mock the DB connection.
- `OAuth2PasswordBearer` has `auto_error=True` by default, meaning FastAPI raises the 401 for missing headers before `get_current_user` even runs. This is the correct behavior, but worth confirming the response format matches expectations.
- `decode_access_token` in `core/security.py` catches `JWTError` and returns `None` rather than raising — need to confirm `get_current_user` properly converts that `None` into a 401 and doesn't silently pass through.

### Edge cases
- **Expired token where `exp` claim is present but already past:** middleware checks expiry manually after `decode_access_token` returns — need to confirm this path raises 401 and not 500.
- **Token with valid signature and format but no `sub` claim:** `user_id = payload.get("sub")` returns `None`, which should trigger `credentials_exception` — this is a separate edge case worth adding as a bonus test.
- **Token signed with correct secret but for a user ID that doesn't exist in the DB:** `scalar_one_or_none()` returns `None`, which should raise 401 — another distinct failure mode to handle.
