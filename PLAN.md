## Solution plan

**Issue:** [Add integration tests for authentication edge cases](https://github.com/ascherj/pathreview/issues/90)

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
The root cause of the issue is that existing tests for tokens only cover whether or not a token is valid — there are no tests that exist to capture the presence of expired tokens, malformed tokens, missing `Authorization` header, and tokens signed with a different secret being *rejected*.

**Expected behavior:** all four bad-token cases should return 401 Unauthorized, since `get_current_user()` (api/middleware/auth.py) is the single dependency guarding every protected route.

**Actual behavior, confirmed by manual reproduction against a running instance:**
all four cases already return 401 correctly — the middleware itself is not broken. The gap is purely a lack of test coverage, not a security bug:

| Case | Response |
|---|---|
| Valid token (baseline) | Passes auth (404 on a nonexistent profile, not 401) |
| Missing `Authorization` header | 401 "Not authenticated" |
| Malformed token | 401 "Invalid authentication credentials" |
| Token signed with wrong secret | 401 "Invalid authentication credentials" |
| Expired token | 401 "Invalid authentication credentials" |

One discrepancy worth noting: the expired-token case returns the generic "Invalid authentication credentials" message rather than the more specific "Token has expired" message that a separate branch of `get_current_user` appears to handle. Tracing the code shows `decode_access_token()` (core/security.py) already catches `jose.ExpiredSignatureError` (a subclass of `JWTError`) and returns `None` before that branch is ever reached — so the "Token has expired" branch is currently dead code for real tokens. This doesn't affect security (still a correct 401), just the specificity of the error message. Flagging it as a possible follow-up rather than in-scope for this tests-only issue.

### Map
<!-- Which files, functions, or modules are involved?
List the specific files you expect to touch. -->
- `tests/integration/test_auth_middleware.py` — does not exist yet; will be
  created new. This is the only file that needs to change.
- Read-only references (no changes expected):
  - `api/middleware/auth.py` — `get_current_user()`, the dependency under test
  - `core/security.py` — `create_access_token()` / `decode_access_token()`,
    used to build valid/expired tokens and understand decode failures
  - `api/routes/profiles.py` — has a `GET /{profile_id}` route, a convenient
    protected endpoint to test against without needing extra setup
  - `tests/conftest.py` — check whether a DB session / test client fixture
    already exists here before adding a new one

<!-- ### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. Set up a shared fixture for an authenticated test user (create a `User`
   row in the test DB, return both the user and a valid token for it) —
   check `tests/conftest.py` first in case something reusable exists.
2. Write the baseline valid-token test to confirm the fixture works end to end.
3. Write the 4 edge-case tests, asserting `401` for each, using the exact
   commands/results already confirmed manually:
   - missing header
   - malformed token
   - wrong-secret token
   - expired token
4. Run `make test-integration`, confirm all 5 pass.
5. Run `make check` (lint/format/typecheck) before opening the PR.

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
- Input: HTTP requests to a protected route (`GET /profiles/{id}`) with
  varying `Authorization` header states (valid, missing, malformed, wrong
  secret, expired).
- Output: this is a test-only change — no production code changes. The
  "output" is a passing test suite that locks in the already-correct 401
  behavior, so a future regression would be caught by CI instead of going
  unnoticed.

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
- Don't yet know if `tests/conftest.py` or elsewhere already has a
  DB-backed test client / test user fixture — need to check before writing
  a duplicate one.
- Integration tests are marked as requiring Docker services per
  `pyproject.toml` — need to confirm `docker compose up -d` is sufficient
  for the test DB, or if there's separate test-only config.
- The expired-token case's dead-code finding (generic message instead of
  "Token has expired") is out of scope to fix, but the test needs to assert
  the *actual* current message, not the one the code seems to intend —
  otherwise the test would fail for the wrong reason.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
- Token with a valid signature but for a user ID that doesn't exist in the
  DB (not explicitly in the issue, but worth a quick check since
  `get_current_user` has a distinct code path for "user not found")
- Token with no `sub` claim at all
- `Authorization` header present but with the wrong scheme (e.g. `Basic`
  instead of `Bearer`)