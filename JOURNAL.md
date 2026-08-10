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

### Check-in 1 

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

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/909

**Branch:** `test/90-auth-edge-cases`

**What you built:**

I added integration test coverage for authentication edge cases on
protected PathReview API routes. The tests verify that requests with a
missing Authorization header, malformed token, expired token, or token
signed with the wrong secret receive a 401 Unauthorized response.

**Tests added or updated:**

I created `tests/integration/test_auth_middleware.py` with four tests
covering:

- Missing Authorization header
- Malformed JWT
- Expired JWT
- JWT signed with the wrong secret

All four targeted integration tests pass.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

The repository had pre-existing failures before my changes.
`make check` reported 182 existing Ruff violations. `make test-unit`
reported 345 passing tests, 52 failures, and 31 errors. My targeted
integration tests pass, and Ruff and Black pass for the new test file.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer feedback was provided. For Summer 2026, reviewer feedback is not part of the PathReview process, so I completed my reflection based on my implementation, testing, and self-review.

**How you responded:**

N/A — no reviewer feedback was received.

---

### Reflection

**What was harder than you expected?**

The hardest part was not writing the four authentication tests themselves. The harder part was understanding enough of an unfamiliar codebase to know where the tests belonged and how authentication moved through the application.

At first, the issue referenced `tests/integration/test_auth_middleware.py`, but that file did not exist yet. I had to trace the authentication flow through `api/middleware/auth.py`, `core/security.py`, `api/main.py`, the protected review routes, and the existing unit tests before I understood what the integration tests needed to exercise.

I also did not expect the repository to already contain so many failing checks. Before making my changes, `make check` reported 182 existing Ruff violations, while `make test-unit` collected 428 tests with 345 passing, 52 failing, and 31 errors. Later, the pre-commit mypy hook also failed because of existing type errors in production files. Learning how to separate problems caused by my work from problems that already existed was one of the most challenging parts of the project.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase is very different from building my own project from scratch. In my own project, I usually know where everything is because I created the structure. In PathReview, I first had to understand how several existing pieces connected before changing anything.

For Issue #90, I followed the request from the protected `/reviews` endpoint to the `get_current_user()` authentication dependency and then to `decode_access_token()`. I also read the existing security unit tests to understand what was already covered before adding new tests.

I learned the importance of making small, focused changes. My final implementation added only `tests/integration/test_auth_middleware.py` instead of changing authentication code or creating unnecessary shared fixtures.

I also learned why establishing a baseline before making changes is important. Because the repository already had failing tests and lint/type-checking problems, recording those failures beforehand allowed me to show that my contribution did not introduce them.

**How did AI tools help — and where did they fall short?**

AI tools were most helpful for navigating the unfamiliar repository and helping me understand how different modules connected. I used AI to inspect the authentication flow, compare the existing unit tests with the integration tests required by the issue, and determine that FastAPI's `TestClient` was a reasonable choice for the new test file.

Codex also helped generate the initial integration tests and run targeted checks. However, I still needed to verify its output instead of accepting it automatically. For example, one test run initially used an environment that did not have FastAPI installed, so I had to make sure the tests were run using the project's virtual environment. I also had to distinguish direct errors in my new file from the many pre-existing mypy errors in imported production files.

The project showed me that AI can speed up exploration and implementation, but I still need to understand what the code is doing, verify commands and test results, and decide whether a suggested change actually belongs in the scope of the issue.

**What would you do differently if you started over?**

I would establish the repository baseline much earlier. Running `make check` and `make test-unit` before doing deeper implementation work would have immediately shown me which failures already existed and saved some uncertainty later.

I would also spend more time at the beginning reading the contribution guide, existing test patterns, and the exact files connected to the issue before planning the implementation.

I would open the draft PR earlier as well. Even though reviewer feedback was not available for Summer 2026, creating the draft earlier would have made the final submission process less rushed.

Most importantly, I would continue breaking the issue into small steps instead of trying to understand the entire PathReview application at once. Tracing one flow at a time was much more effective.

**What are you most proud of from this module?**

I am most proud that I was able to contribute to a codebase that initially felt much larger and more complicated than the projects I had built myself.

I started by setting up PathReview locally, troubleshooting Docker, PostgreSQL, Node, and npm, and eventually getting the complete application running. I then traced the authentication system, reproduced all four edge cases manually, created a solution plan, and implemented four passing integration tests for missing, malformed, expired, and incorrectly signed authentication tokens.

My final contribution stayed focused on the issue instead of changing unrelated production code. More than just getting four tests to pass, I am proud that I learned how to investigate an unfamiliar system, document what I found, distinguish my own failures from pre-existing ones, and submit a real pull request with evidence supporting my changes.