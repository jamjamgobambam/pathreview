## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90

**Issue title:** Add integration tests for authentication edge cases

**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, tests for auth middleware check if a token is valid or not. However, these tests do not include edge cases like expired tokens, malformed tokens, tokens assigned with a different secret, and missing `Authorization` headers, all of which follow a valid token format but aren't tokens that can be used. This PR adds those edge cases into the unit tests to ensure the bad tokens can be caught instead of silently ignored. 

**Branch name:** feat/90-auth-edge-cases-tests

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/atile4/pathreview/commit/f26aa836567c233fd32890817addbad87abf3679

**Reproduction steps:**
1. Started the app locally (`make run`) and registered a test user via
   `POST /auth/register` to get a valid token.
2. Confirmed a baseline: `GET /profiles/{uuid}` with the valid token returns
   404 "not found" (not 401) — proves the happy path passes auth correctly.
3. Triggered each missing case by hand against the same route:
   - No `Authorization` header → `401 "Not authenticated"`
   - Malformed token (`Bearer not-a-real-jwt`) → `401 "Invalid authentication credentials"`
   - Token signed with a different secret (forged via a throwaway script using
     `jose.jwt.encode` directly) → `401 "Invalid authentication credentials"`
   - Expired token (forged via `create_access_token` with a negative
     `expires_delta`) → `401 "Invalid authentication credentials"`
4. Result: all four cases are already handled correctly by the middleware
   (each returns 401) — this is a test-coverage gap, not a security bug.
5. Found one discrepancy while tracing the code: the expired-token case
   returns the generic "Invalid authentication credentials" message instead
   of the more specific "Token has expired" message a separate branch of
   `get_current_user` appears to produce. `decode_access_token()` already
   catches expired tokens via `jose.JWTError` and returns `None` before that
   branch runs, so it's currently unreachable dead code. Flagged as a
   possible follow-up, not fixed here.

**PLAN.md link:** https://github.com/atile4/pathreview/blob/feat/90-auth-edge-cases-tests/PLAN.md

<!-- **Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded] -->

**Blockers or open questions:**
<!-- [Anything you're still uncertain about going into Week 9, or leave blank] -->

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the two sub-tasks from PLAN.md that make up the actual fix:
`tests/integration/conftest.py` (shared fixtures — a DB-backed `test_user`,
a valid `auth_token`, and an `httpx.AsyncClient` wired to the app) and
`tests/integration/test_auth_middleware.py` (5 tests: baseline valid-token
pass, missing header, malformed token, wrong-secret token, expired token).
No changes to `api/middleware/auth.py` or `core/security.py`, per the
"not in scope" note in PLAN.md.

**Next steps:**
Confirm `make test-integration` and `make check` pass in my own local
environment [confirm this — you were last debugging a missing
`.venv/bin/alembic`], then open a draft PR for review.

**Blockers:**
Using `make setup` and `make run` was not working as intended

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/464

**Branch:** feat/90-auth-edge-cases-tests

**What you built:**
Added integration test coverage for `get_current_user()` (the auth
dependency guarding every protected route), covering four previously
untested edge cases — expired, malformed, and wrong-secret tokens, plus a
missing `Authorization` header — alongside a valid-token baseline. All five
were manually reproduced against a running instance beforehand (see Week 8
entry); the middleware was already correct, so this closes a test-coverage
gap rather than fixing a bug.

**Tests added or updated:**
- `tests/integration/conftest.py` (new) — `test_user`, `auth_token`,
  `client` fixtures, plus an autouse fixture disposing the SQLAlchemy
  engine's connection pool between tests (needed to avoid cross-event-loop
  asyncpg errors under pytest-asyncio's per-test event loops).
- `tests/integration/test_auth_middleware.py` (new) — 5 tests against
  `GET /profiles/{profile_id}`, asserting the exact status codes/messages
  confirmed during Week 8 reproduction.

**Self-review confirmation:** [✅] make check passes  [✅] make test-unit passes
[Check these only once you've actually run them yourself and confirmed —
note any pre-existing failures you saw and that your branch doesn't add
new ones, per the "Pre-existing failures" guidance above]

**Draft PR feedback received from:** none