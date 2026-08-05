## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90

**Issue title:** Add integration tests for authentication edge cases

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**

The authentication system has tests showing that valid tokens can be
created and decoded, but it does not have integration tests proving
that protected API routes reject invalid authentication attempts.
The missing cases include expired tokens, malformed tokens, requests
without an Authorization header, and tokens signed using a different
secret. A successful solution will add integration tests that send
these requests to a protected endpoint and verify that each request
receives a 401 Unauthorized response.

**Branch name:** test/90-auth-edge-cases

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Is this issue right for me? — Selection notes

I can explain the issue and the expected behavior in my own words. I
located the authentication middleware in `api/middleware/auth.py`, the
JWT functions in `core/security.py`, and the existing security unit
tests in `tests/unit/test_security.py`. I confirmed that the requested
integration test file does not currently exist, so creating
`tests/integration/test_auth_middleware.py` will be part of the work.

This is a Tier 2 issue, which is more challenging than the recommended
Tier 1 starting point. However, the scope is focused on authentication
tests rather than creating an entirely new application feature. The
issue is estimated at three to five hours, and the four required test
cases are clearly identified. I chose it because it will help me learn
how the API, middleware, JWT security functions, and test client work
together while keeping the work limited to one specific area.

At the time I claimed the issue, I did not see an assignee or a stated
dependency blocking the work. I will complete the tests one case at a
time and ask for clarification if the integration-test setup requires
changes outside the expected scope.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

I completed the local reproduction and solution plan for Issue #90.
I reviewed the authentication dependency in
`api/middleware/auth.py`, the JWT utilities in `core/security.py`,
and the existing security unit tests.

I also established the pre-change baseline before implementing the
new integration tests.

`make check` currently fails with 182 pre-existing Ruff violations
across the repository.

`make test-unit` currently reports:

- 428 tests collected
- 345 passed
- 52 failed
- 31 errors
- 1 warning

These failures appear unrelated to Issue #90. The only existing
security test failure concerns malformed bcrypt-hash handling, not
JWT authentication or protected API routes.

The working tree remained unchanged after running the baseline checks.

**Next steps:**

Create `tests/integration/test_auth_middleware.py` and add integration
tests for:

- Missing Authorization header
- Malformed JWT
- Expired JWT
- JWT signed with the wrong secret

Then run the new integration test file and compare the final project
checks against the recorded baseline.

**Blockers:**

The repository currently has pre-existing lint, unit-test, and test
setup failures. I will document these in the PR and confirm that my
changes do not introduce additional failures.