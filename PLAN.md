# Issue #90 Solution Plan

## Issue Summary

PathReview protects API routes using JWT authentication, but the repository does not currently include integration tests for several important authentication failures.

The missing cases are:

- A request with no Authorization header
- A request with a malformed token
- A request with an expired token
- A request with a token signed using the wrong secret

The application currently rejects these requests correctly. The goal of this issue is to add automated integration tests so that future changes do not accidentally weaken the authentication middleware.

## Reproduction

I reproduced the issue locally using the protected `GET /reviews`
endpoint.

### 1. Missing Authorization Header

Command:

```bash
curl -i http://localhost:8000/reviews
```

Observed result:

```text
HTTP/1.1 401 Unauthorized
{"detail":"Not authenticated"}
```

### 2. Malformed Token

Command:

```bash
curl -i \
  -H "Authorization: Bearer not_a_jwt_token" \
  http://localhost:8000/reviews
```

Observed result:

```text
HTTP/1.1 401 Unauthorized
{"detail":"Invalid authentication credentials"}
```

### 3. Expired Token

I generated a correctly signed JWT using `create_access_token()` with an expiration time one minute in the past. I then sent the token to the protected endpoint.

Observed result:

```text
HTTP/1.1 401 Unauthorized
{"detail":"Invalid authentication credentials"}
```

### 4. Token Signed With the Wrong Secret

I generated a valid JWT structure using the configured JWT algorithm, but signed it with a different secret. I then sent the token to the protected endpoint.

Observed result:

```text
HTTP/1.1 401 Unauthorized
{"detail":"Invalid authentication credentials"}
```

## Reproduction Conclusion

The application currently rejects all four invalid authentication cases correctly. However, this behavior is only verified manually.

Automated integration tests are needed to prevent authentication regressions.

## Relevant Code

I inspected the following files:

- `api/main.py`
  - Creates the FastAPI application and includes the API routers.

- `api/middleware/auth.py`
  - Defines `get_current_user()`, which reads the bearer token and
    rejects invalid authentication requests.

- `core/security.py`
  - Defines `create_access_token()` and `decode_access_token()`.

- `tests/unit/test_security.py`
  - Contains unit tests for token creation and decoding.

- `tests/conftest.py`
  - Contains shared test fixtures, but it does not currently include
    an API client or authentication integration fixtures.

- `tests/integration/__init__.py`
  - Confirms that the integration-test directory exists, but no
    authentication integration test file currently exists.

## Proposed Solution

I will create:

`tests/integration/test_auth_middleware.py`

The new test file will send HTTP requests to the protected
`GET /reviews` endpoint through the FastAPI application defined in
`api/main.py`.

The test file will cover these four cases:

1. A request without an Authorization header returns 401.
2. A request with a malformed token returns 401.
3. A request with an expired token returns 401.
4. A request with a token signed using the wrong secret returns 401.

For the malformed-token test, I will send a value such as
`not_a_jwt_token`.

For the expired-token test, I will use `create_access_token()` with an
expiration time in the past.

For the wrong-secret test, I will use `jose.jwt.encode()` with the configured JWT algorithm but a different signing secret.

The tests will verify the HTTP status code and the response detail.

The missing-header test should expect `Not authenticated`. The other three tests should expect `Invalid authentication credentials`, based on the behavior reproduced locally.

## Expected File Changes

### New file

- `tests/integration/test_auth_middleware.py`
  - Adds the four authentication edge-case integration tests.

### Possible supporting change

- `tests/conftest.py`
  - May need a reusable API test-client fixture if the project testing
    setup requires one.

I will avoid changing production authentication code unless the tests reveal behavior that contradicts the issue requirements.

## Test Strategy

I will first run only the new integration test file:

```bash
pytest tests/integration/test_auth_middleware.py -v
```

After the new tests pass, I will run the required project checks:

```bash
make check
make test-unit
```

I will also run the complete test suite if the repository setup allows
it:

```bash
pytest
```

## Risks and Known Unknowns

- The repository currently has no API integration-test client fixture, so I need to confirm the correct test-client pattern.
- Importing the FastAPI application may trigger startup behavior or database initialization.
- The tests should avoid relying on production database records because invalid authentication should be rejected before protected route logic is executed.
- The expired-token response is currently
  `Invalid authentication credentials` because token decoding rejects the token before the middleware reaches its separate expiration check.
- I need to verify whether the maintainers prefer synchronous
  `TestClient` tests or asynchronous HTTP client tests.

## Definition of Done

The issue will be complete when:

- `tests/integration/test_auth_middleware.py` exists.
- All four authentication edge cases have automated tests.
- Every invalid authentication request returns 401.
- The new tests pass consistently.
- Existing unit tests continue to pass.
- `make check` completes successfully.
- No unrelated production behavior or files are changed.