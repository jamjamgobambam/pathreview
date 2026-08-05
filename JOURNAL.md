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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [✅] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The most unexpectedly difficult part of this setting up. I had issues with running `make setup` and `make run`,  as I didn't know I needed Docker to be running, and I also had trouble with the Python version not being correct, which lead me down a rabbit hole of Python being half installed such that I couldn't reinstall it nor could I delete it. 


**What did you learn about working in a large codebase?**
Working in a much larger codebase compared to my own felt like navigating a new country. I could understand the code (kind of) like I could recognize buildings/people, but the overall structure was foreign and I didn't know what was going on, and how files connected. Still, through these past weeks, learning to work in this environment taught me that at the very least, having a rock-solid understanding of one part of the codebase that encompasses my task is significantly better than having a shallow understanding of the entire codebase, because I'd still be able to get the task done without missing anything.

**How did AI tools help — and where did they fall short?**
AI tools like Claude and Copilot were extremely helpful in helping me to navigate the codebase. It helped me to understand what files did, how different files connected, and pointed me towards where the issue needed to be fixed. 

However, those tools didn't help me much when I was trying to fix push issues. I had difficulty committing because of the automated checks that needed to be ran, and AI tools weren't very helpful in deciphering the warnings that were returned, nor was it helpful in figuring out why they were going wrong. I had to go through the documentation to figure out that the errors were pre-existing, and had to ignore them in order to be able to push my changes.

**What would you do differently if you started over?**
If I started over, I'd create a document, or a Google Doc for notes, outlining all the connectors between files. I'd also extensively note down my task, what was required of my task, like related files, paths to those files, and what those files did, to ensure I had a good understanding of the issue. 

**What are you most proud of from this module?**
From all I did in this module, I was most proud of writing my final pull request. That PR was a culmination of all my work across the past three weeks, and it felt extremely satisfying breaking down my work, writing out what I did, and sending it off to be reviewed and merged. Seeing everything I'd built come together into one clean, well-documented submission made all the earlier tests and iteration feel worth it.
