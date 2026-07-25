# Solution plan

**Issue:** Add integration tests for authentication edge cases —
https://github.com/ascherj/pathreview/issues/90

### Understand

This is a test-coverage gap, not a behavior bug. The JWT auth middleware
(`api/middleware/auth.py::get_current_user`) guards every protected route,
but the only auth-related tests in the repo (`tests/unit/test_security.py`)
cover the token *helper functions* in isolation. Nothing tests the
middleware's HTTP contract, and `tests/integration/` is empty.

- **Expected:** each rejection path — expired token, malformed token, missing
  `Authorization` header, token signed with a different secret — is locked in
  by an integration test asserting the 401 response.
- **Actual (reproduced 2026-07-19, see JOURNAL Week 8):** all four paths
  return 401 correctly today, but zero tests exercise them, so a regression
  would ship unnoticed.

### Map

Files to **create**:
- `tests/integration/test_auth_middleware.py` — the only file the PR adds.

Files to **read/exercise** (no changes):
- `api/middleware/auth.py` — `get_current_user`, the code under test
- `core/security.py` — `create_access_token` (negative `expires_delta`
  forges expired tokens), `decode_access_token`
- `api/routes/auth.py` — `POST /auth/register` to create a real user fixture
- `api/routes/profiles.py` — `GET /profiles/{id}` as the protected route
- `core/config.py` — `settings.secret_key` / `jwt_algorithm` for the
  wrong-secret case (signed via `jose.jwt.encode` with a different key)

### Plan

1. **Fixtures:** module-scoped `TestClient(api.main.app)` against the real
   Dockerized Postgres (context manager triggers startup/table creation), and
   a `registered_user` fixture that registers a unique user via
   `POST /auth/register` and returns their id + token.
2. **Issue cases:** one test class per case — missing header, malformed
   token (parametrized variants), expired token, wrong-secret token — each
   asserting 401 plus the `WWW-Authenticate: Bearer` header and response detail.
3. **Baseline:** valid-token test asserting 404 (not 401) on a random profile
   id, proving the request passed the middleware — this cleanly separates
   "rejected by middleware" from "route-level failure".
4. **Adjacent edge cases** (see below) to fully lock in the contract.
5. **Verify:** `make test-integration`, `ruff check`, `ruff format`, and
   mypy-clean annotations on the new file (`disallow_untyped_defs` is on).

### Inputs & outputs

- **Inputs:** crafted JWTs (valid, expired, forged, mangled) and raw HTTP
  requests sent to a protected endpoint on the real app with a real database.
- **Outputs:** one new test module (~15 tests) that pins the middleware's
  observable contract: 401 + `WWW-Authenticate: Bearer` for every bad
  credential, and pass-through for valid ones. **No application code changes**
  — if any test fails, that's a middleware bug to fix, not a test to adjust.

### Risks & unknowns

- **Fresh-DB startup crash (pre-existing):** `core/models/profile.py`
  declares `ix_profiles_user_id` twice, so `init_db()`/`create_all` fails on
  an empty database — migrations (`alembic upgrade head`) must run before
  tests. Documented in JOURNAL; will file as a separate issue.
- **Dead expiry branch:** expired tokens are rejected inside
  `decode_access_token` (jose validates `exp`), so the middleware's explicit
  `"Token has expired"` branch (auth.py:44–49) never runs. Tests must assert
  the observable behavior (generic 401), not that branch. Cleaning it up is
  out of scope for a test-only PR.
- **Broken pre-commit mypy hook:** fails on ~65 pre-existing errors in
  `api/`/`core/` (CI typecheck is red on main for the same reason);
  Python commits need `--no-verify` for now.
- **Event-loop pitfalls:** pytest-asyncio + the module-level async engine can
  produce cross-loop connection errors; using the synchronous `TestClient`
  with module scope (one loop for the whole module) avoids this entirely.

### Edge cases

Beyond the four cases in the issue, the suite should handle:

- empty bearer value (`Authorization: Bearer `)
- wrong scheme carrying a valid token (`Basic <token>`)
- tampered payload segment (signature no longer matches)
- stripped signature segment (unsigned token)
- syntactically valid, correctly signed token **missing the `sub` claim**
- correctly signed token whose `sub` is a **user that doesn't exist** in the DB
- near-expiry but still-valid token (must NOT be rejected — guards against
  over-eager expiry logic)
