## Solution plan

**Issue:** Add integration tests for authentication edge cases — https://github.com/ascherj/pathreview/issues/90

> **Revised 2026-08-01.** The original plan (2026-07-26) scoped this to four rejection paths and
> excluded happy-path coverage. That was wrong, and the revision history at the bottom of this
> file records why. The plan below is the one being implemented.

### Understand

The issue states that "the auth middleware is tested with a valid token but there are no tests
for" four rejection cases. The premise is false. No test in the repository references
`get_current_user` at all — a `grep` across `tests/` returns zero hits, and `tests/integration/`
contained only `__init__.py`. What exists is `tests/unit/test_security.py`, which tests the JWT
helpers (`create_access_token`, `decode_access_token`) in isolation. Those prove the decoder
returns `None` for bad input; nothing proves the middleware refuses entry to a protected route
when it does.

So the real gap is wider than the issue describes: `get_current_user` has no coverage at all,
neither its rejection paths nor its success path.

- **Expected:** each way of presenting a credential to a protected route, good or bad, is pinned
  by a test that fails if the middleware's behavior changes.
- **Actual:** none of it is covered. A regression letting unauthorized requests through would pass
  silently, and so would one rejecting every request.

That second failure mode is why rejection-only testing is insufficient: a middleware replaced with
an unconditional `raise HTTPException(401)` would satisfy every rejection test. The success path is
what gives the rejection tests meaning.

**Root cause:** No test exercises `get_current_user` (`api/middleware/auth.py`), and
`tests/integration/` has no fixture infrastructure with no app client, no persisted user, no token.

### Map

- `tests/integration/conftest.py` *new* - Shared fixtures: an `async_client`
  (`httpx.AsyncClient` over `ASGITransport`), a `test_user` that persists a real row and removes it
  afterwards, and an `auth_token` signing a valid JWT for that user with the app's own helper.
- `tests/integration/test_auth_middleware.py` — **the test module.** Seven tests, thirteen
  parametrized cases.
- Read-only references (not edited):
  - `api/middleware/auth.py` — `get_current_user`, the subject.
  - `core/security.py` — `create_access_token` / `decode_access_token`; used to forge test JWTs.
  - `core/database.py` — `get_db`, `AsyncSessionLocal`; the session the fixtures write through.
  - `core/models/user.py` — the `User` row the happy path needs.
  - `api/routes/reviews.py` — `GET /reviews`, the protected route under test.
  - `api/main.py` — the `app` the clients wrap.
  - `.venv/.../fastapi/security/oauth2.py` — `OAuth2PasswordBearer.__call__`, which owns the
    `"Not authenticated"` response *before* `get_current_user` runs.

### Plan

Coverage is derived from the exits of `get_current_user`, not only from the issue's bullet list.
Enumerating them (full trace in `personal/TRACE_AUTH_REQUEST.md`) gives eight; five are reachable
without simulating infrastructure failure. The three uncovered are out of scope for this specific issue and will require additional issues to be resolved.

1. **Bring up real infrastructure.** `docker compose up -d db`, `make migrate`. The
   `integration` marker is defined in `pyproject.toml:87` as *"require Docker services"*, so these
   tests use a real Postgres rather than a stubbed session.
2. **Build the fixtures** in `tests/integration/conftest.py`: `async_client`, `test_user`,
   `auth_token`.
3. **Exit 1 — absent credential** → `401 "Not authenticated"`. Parametrized: no `Authorization`
   header, and a non-`Bearer` scheme (`Basic ...`).
4. **Exit 2 — undecodable token** → `401 "Invalid authentication credentials"`. Parametrized:
   `not.a.jwt`, `a.b`, `aaa.bbb.ccc`, and the empty string (`Authorization: Bearer ` with no token).
5. **Exit 2 — expired token** → same generic message. Forged with
   `create_access_token(..., expires_delta=timedelta(minutes=-5))`.
6. **Exit 2 — bad signature or algorithm** → same generic message. Parametrized: a JWT signed with
   a foreign secret; one signed with the *correct* secret but `HS512`; and a hand-assembled
   `alg=none` forgery, which `jose.encode` refuses to build and which must therefore be
   constructed from base64 segments the way an attacker would.
7. **Exit 3 — valid token, no `sub` claim** → same generic message. The only rejection that gets
   *past* `decode_access_token`, raising at `auth.py:40-41`.
8. **Exit 7 — valid token for a user that does not exist** → same generic message, raised at
   `auth.py:68-69` after the database query returns nothing. Requires the database.
9. **Exit 8 — happy path.** A valid token for a persisted user returns `200`. Requires the
   database and the `test_user` fixture.
10. **Verify and document.** Scoped `black` / `ruff` on the new files; `make test-integration`
    green with zero skips; `make check` and `make test-unit` compared against the pre-change
    baseline (182 lint errors; 53 failed / 375 passed) to confirm no new failures.

### Inputs & outputs

- **Inputs:** HTTP requests to `GET /reviews` carrying an `Authorization` header. The header value
  is either absent, a wrong scheme, or a `Bearer` token built one of four ways — by the app's own
  `create_access_token` (valid, expired, or claimless), by `jose.jwt.encode` with a foreign secret
  or non-whitelisted algorithm, by hand from base64 segments (`alg=none`), or by hand as a literal
  junk string. The database-backed tests additionally insert a `User` row before the request.
- **Outputs:** `httpx.Response` objects. Tests assert `response.status_code` (`401` for seven
  cases, `200` for the happy path) and `response.json()["detail"]` — `"Not authenticated"` for
  exit 1, `"Invalid authentication credentials"` for exits 2, 3 and 7.
- **No production code changes.** No signature, no runtime behavior, no dependency is modified.
  The diff is two test files.

### Risks & unknowns

- **Cross-event-loop `asyncpg` failures — the main technical risk, and it materialised.**
  pytest-asyncio creates a fresh event loop per test, while `core/database.py:11` builds a
  module-level pooled engine shared across all of them. A connection opened in one test's loop is
  returned to the pool, outlives that loop, and then fails `pool_pre_ping` in the next test with
  `got Future ... attached to a different loop`. Resolved by calling `await engine.dispose()` on
  entry to both async fixtures, so every connection belongs to the current loop. Every test uses
  `httpx.AsyncClient` over `ASGITransport` rather than a mix of sync and async clients, which keeps
  one client and one pattern across the module.
- **Test isolation against a real database.** `test_user` writes a row to a shared dev database and
  must remove it on teardown, including when the test fails. A leaked row with a unique `email`
  breaks the next run.
- **The `"Token has expired"` branch (`auth.py:44-49`) is unreachable.** `decode_access_token`
  (`core/security.py:78-86`) catches every `JWTError`, `ExpiredSignatureError` among them, and
  returns `None` — so `auth.py:35` fires first and expired tokens get the generic message. The test
  asserts observed behavior, not intended behavior.
- **That assertion is coupled to a defect.** If the unreachable expiry branch is ever repaired so
  that expired tokens return `"Token has expired"`, this one assertion will need updating. I am
  pinning today's real behavior deliberately and flagging it in the PR rather than pre-empting a
  fix that belongs in its own change.

### Edge cases

1. **Absent header vs. present-but-wrong scheme.** No `Authorization` at all and
   `Authorization: Basic ...` both yield `401 "Not authenticated"` from `OAuth2PasswordBearer` —
   a different code path and message from every token case.
2. **`Bearer` with an empty token.** `Authorization: Bearer ` is **not** treated as a missing
   credential. `get_authorization_scheme_param` splits on the space, the scheme is legitimately
   `bearer`, and an empty string is passed on to be decoded — so it returns
   `"Invalid authentication credentials"`, not `"Not authenticated"`.
   *(The original plan predicted the opposite; probing the running app corrected it.)*
3. **Structurally malformed vs. cryptographically invalid.** `not.a.jwt` and a well-formed token
   signed with the wrong secret are different failure modes that must both be refused.
4. **Algorithm confusion.** A token declaring `alg=none` with an empty signature — the classic JWT
   forgery — must be rejected by the `algorithms=[HS256]` whitelist. So must a correct signature
   made with `HS512`. `jose.encode` refuses to produce an `alg=none` token, so the test builds it
   by hand; the library's refusal proves nothing about the application.
5. **Expired token returns the generic message.** Asserting that exact string is what pins the
   dead expiry branch, and what will fail loudly if that branch is ever repaired.
6. **Valid, correctly signed token carrying no `sub` claim.** Decodes cleanly, then fails the
   claim check — the only rejection reaching `auth.py:40-41`.
7. **Valid token for a user absent from the database.** Signature and claims are fine; the lookup
   returns nothing and the request is refused at `auth.py:68-69`.
8. **Valid token for a user that exists** returns `200`. Without this case the suite cannot
   distinguish correct rejection from blanket rejection.

---

### Revision history

**2026-08-01 — scope corrected.** The original plan covered only the four rejection paths named in
the issue and kept happy-path and user-not-found tests out of scope on the grounds that they
needed a shared user fixture this repo doesn't have. Two things were wrong with that:

- **The suite it produced could not fail correctly.** Six passing rejection tests would all still
  pass against a middleware that rejected every request unconditionally, valid credentials
  included. The success path is what makes rejection tests meaningful. This is helpful as a unit test
  but not a full integration test.
- **The fixture was not actually blocked.** Nothing prevented a fixture local to
  `tests/integration/` — it needed writing, not waiting on.

The original plan also assumed these tests should avoid docker services, which contradicts
`pyproject.toml:87` — the `integration` marker is defined as *"require Docker services."*

Coverage was re-derived from the exits of `get_current_user` rather than from the issue's bullet
list, taking the plan from 4 scenarios to 8 across 5 of the function's 8 exits. The three not
covered are two unreachable branches and a database-failure path, all documented as findings in
the PR rather than tested.