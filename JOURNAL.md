# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90

**Issue title:** Add integration tests for authentication edge cases

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The auth middleware currently only has coverage for the happy path — a single
request carrying a valid JWT. That leaves every failure mode untested, so a
regression in how the API rejects bad credentials could ship unnoticed. This
issue asks for integration tests covering the rejection paths: an expired
token, a malformed/garbage token, a completely missing `Authorization` header,
and a token that is well-formed but signed with the wrong secret. A successful
fix adds these cases to `tests/integration/test_auth_middleware.py`, each
asserting the middleware returns the correct 401 response, so the auth layer's
guarantees are locked in against future changes.

**Branch name:** test/90-auth-middleware-edge-cases

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Nikayel/pathreview/commit/75c3b7c8cfda2623a03a62dd33f02baeb2143992

**Reproduction summary:**
Confirmed the coverage gap: `pytest tests/integration -m integration` runs
zero tests, and no test in the repo exercises `get_current_user` or sends an
`Authorization` header. I then hit a protected endpoint on the locally
running API with each credential the issue lists — all four rejection paths
work but are completely untested.

**Reproduction steps:**

1. Environment: corrected `upstream` to `ascherj/pathreview` and rebased on
   `upstream/main`; `docker compose up -d db` (Postgres 16, host port 5433);
   `.env` from `.env.example`; `alembic upgrade head` (revisions 001, 002).
2. Show the gap:
   - `pytest tests/integration -m integration` → `no tests ran`
   - `grep -rl "get_current_user\|Authorization" tests/` → no matches
     (`tests/unit/test_security.py` covers the token helper functions, but
     nothing tests the middleware's HTTP contract)
3. Exercise the untested paths against the running API
   (`uvicorn api.main:app`), `GET /profiles/<random-uuid>`:

   | Credential | Observed response |
   |---|---|
   | valid token (registered user) | 404 `{"detail":"Profile not found"}` — passes middleware |
   | no Authorization header | 401 `{"detail":"Not authenticated"}` |
   | malformed token (`not-a-jwt`) | 401 `{"detail":"Invalid authentication credentials"}` |
   | expired token (`expires_delta=-5min`) | 401 `{"detail":"Invalid authentication credentials"}` |
   | token signed with a different secret | 401 `{"detail":"Invalid authentication credentials"}` |

**Findings while reproducing:**
- The expired token returns the generic message, **not** the middleware's
  dedicated `"Token has expired"` response — `jose.jwt.decode` rejects
  expired tokens inside `decode_access_token` before the explicit expiry
  branch in `api/middleware/auth.py` (lines 44–49) can run. That branch is
  effectively dead code; tests should assert the observable contract.
- Pre-existing bug (out of scope, to file separately):
  `core/models/profile.py` declares the `ix_profiles_user_id` index twice
  (`index=True` on the column + explicit `Index(...)` in `__table_args__`),
  so startup `init_db()` crashes with `DuplicateTableError` on a fresh,
  empty database. Migrations must run first.

**PLAN.md link:** https://github.com/Nikayel/pathreview/blob/test/90-auth-middleware-edge-cases/PLAN.md

**Walkthrough video (recommended):** _to record_

**Blockers or open questions:**
- Should the dead expiry branch in `auth.py` be cleaned up in this PR or
  filed separately? (Planning to file separately — this PR stays test-only.)
- The pre-commit mypy hook fails on ~65 pre-existing annotation errors in
  `api/`/`core/` (CI's typecheck job fails on main for the same reason), so
  Python commits need `--no-verify` until that's fixed upstream.
