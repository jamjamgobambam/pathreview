## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90
**Issue title:** Add integration tests for authentication edge cases
**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
There are currently no integration tests whatsoever for the authentication middleware. The issue identifies four specific gaps: expired tokens, malformed tokens, a missing Authorization header, and tokens signed with a different secret. This matters because right now we have no way to know whether an authentication bug is allowing unauthorized access to protected routes — the middleware is only exercised with a valid token, so any regression in the rejection paths would pass unnoticed. A successful fix means each of those four cases is covered by an automated test that fails if the middleware ever stops rejecting them. Because there are no integration tests in the repository yet, this also establishes the pattern that future integration tests will follow.

**Selection notes:**
I selected this issue because I want to focus on the contribution process as much as the implementation. I'm a professional developer and the code itself is familiar territory, but my commit and merge practices have always been low-key and built on worn-out habits, so getting the contribution side right matters more to me here than picking the hardest available problem. I could potentially contribute at a higher tier, but given time constraints I felt it prudent to prioritize the ability to finish within the timeframe above everything else.

I ultimately decided on Tier 2 to balance the time commitment against doing meaningful work. I rejected #102, a Tier 3 frontend issue estimated at 7–10 hours, even though I would have found it more interesting, in favor of this one at 3–5 hours, both lower risk and smaller scope. Test work also degrades gracefully: if my available hours evaporate, four solid tests is still a complete, mergeable PR, whereas a half-finished feature would be nothing. If I get through this cleanly and come out knowing the codebase better, I can take on a higher tier for a second issue.

I did notice that there are no integration tests whatsoever and conftest.py has no client fixture, so I'll be establishing a pattern rather than following one. That is a front-loaded risk I'm accepting knowingly rather than discovering later. I've worked through the "Is this issue right for me?" checklist and this fits.

**Branch name:** test/90-auth-middleware-edge-cases
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/houdinii/pathreview/commit/968fd45c59b5e328a861136cf41a95b1933410c4

**Reproduction summary:**
This is a test-coverage gap rather than a runtime bug, so I reproduced it by proving the rejection
paths have no coverage today: a grep for `get_current_user` across `tests/` exits 1 (zero hits) and
`tests/integration/` holds only `__init__.py`. I then confirmed the current behavior of each case by
probing the protected `GET /reviews` route — a missing header returns 401 "Not authenticated", while
malformed, expired, and wrong-secret tokens all return 401 "Invalid authentication credentials". The
reproduction commit adds four skipped test stubs naming those cases and documents the confirmed
behavior in its message.

**PLAN.md link:** https://github.com/houdinii/pathreview/blob/test/90-auth-middleware-edge-cases/PLAN.md

**Blockers or open questions:**
None blocking. One boundary I am tracking: issue E-04 ("Authentication middleware doesn't validate
token expiry") may later change the expired-token message from the generic 401 to "Token has
expired", which would require updating my expired-token assertion. I test the current behavior and
note the dependency rather than coupling the two tickets.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implementation is complete. PLAN.md steps 1 through 9 are done and committed as `5998390`, and
step 10 (verification) is finished apart from opening the pull request. I brought up Postgres
(`docker compose up -d db`, `make migrate`), wrote three fixtures in a new
`tests/integration/conftest.py` (`async_client`, `test_user`, `auth_token`), and replaced the four
skipped stubs from Week 8 with seven tests covering thirteen parametrized cases:
absent credential, undecodable token, expired token, bad signature or algorithm, a token with no
`sub` claim, a valid token for a user that does not exist, and a valid token for a user that does.
`make test-integration` reports 13 passed, 0 skipped. Both project baselines are unchanged from
the readings I took before writing any code — `make check` still reports 182 pre-existing ruff
errors and `make test-unit` still reports 53 failed / 375 passed — so this branch introduces no
new failures.

Mid-week I corrected the plan's scope, which is the most significant thing that happened. The
original plan covered only the four rejection paths the issue names and deliberately excluded a
valid-token test. That was wrong: a suite made entirely of rejection tests would pass against a
middleware that rejected *every* request, valid credentials included, so it could not actually
detect the failure it exists to catch. I re-derived coverage from the exits of `get_current_user`
itself rather than from the issue's bullet list, which took the plan from four scenarios to eight
and reached five of the function's eight exits. PLAN.md has been rewritten, with a revision
history recording what changed and why.

**Next steps:**
Update my PR description for the final scope, open the pull request against `ascherj/pathreview`
as a draft, and ask for peer review in Slack. Once feedback is addressed I will mark it ready for
review, add Check-in 2 with the PR link and both self-review confirmations, and submit the branch
URL through the course portal.

**Blockers:**
None. Two things I worked around rather than fixed, both documented for reviewers. First, the
pre-commit mypy hook fails with 44 errors across seven files in `api/` and `core/`; all are
pre-existing, none are in files I touched, and mypy only sees them because my tests import
`api.main`. I committed with `SKIP=mypy` so that ruff and black still ran. Second, adding the
database-backed tests produced a cross-event-loop `asyncpg` failure, because pytest-asyncio
creates a fresh event loop per test while `core/database.py` holds a module-level connection pool;
disposing the pool on fixture entry resolved it.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/601

**Branch:** `test/90-auth-middleware-edge-cases`

**What you built:**
This adds the repository's first integration tests for `get_current_user`
(`api/middleware/auth.py`), the dependency guarding every protected route, which previously had no
test coverage of any kind. Seven tests drive the real FastAPI app and a real Postgres database
through `httpx.AsyncClient`, presenting each kind of credential — absent, undecodable, expired,
wrongly signed, claimless, valid-but-unknown, and valid — to the protected `GET /reviews` route and
asserting the exact status code and error message the middleware returns. No production code
changed; this closes a test-coverage gap rather than fixing a bug.

**Tests added or updated:**
Two new files, both under `tests/integration/`.

`tests/integration/test_auth_middleware.py` holds seven tests, thirteen cases once parametrized,
covering five of the eight ways `get_current_user` can exit:

- `test_absent_credential_returns_401` — no `Authorization` header at all, and a present-but-wrong
  `Basic` scheme. Both assert `401` with the detail `"Not authenticated"`, which comes from
  `OAuth2PasswordBearer` before the middleware runs at all.
- `test_undecodable_token_returns_401` — four bearer tokens the JWT decoder cannot read: a non-JWT
  string, a two-segment token, undecodable base64, and an empty token. All assert `401` with
  `"Invalid authentication credentials"`.
- `test_expired_token_returns_401` — a correctly signed token whose expiry is in the past. It
  asserts the *generic* message rather than the `"Token has expired"` the middleware appears to
  intend, because `decode_access_token` catches the expiry error and returns `None` before that
  branch can run.
- `test_bad_signature_or_algorithm_returns_401` — three forgeries that are structurally perfect and
  unexpired, differing only in how they are signed: a token signed with a foreign secret, one
  signed with the real secret but a non-whitelisted `HS512`, and a hand-assembled `alg=none` token
  with an empty signature. Together these prove the `algorithms=["HS256"]` whitelist is what
  protects the route.
- `test_token_without_sub_claim_returns_401` — a valid, decodable token carrying no `sub` claim.
  This is the only rejection that gets *past* the decoder, reaching the claim check.
- `test_token_for_unknown_user_returns_401` — a valid token whose subject is a well-formed UUID
  with no matching row, so the rejection happens after the database lookup returns nothing.
- `test_valid_token_for_existing_user_returns_200` — a valid token for a user persisted by the
  fixtures reaches the route and returns `200` with an empty result list. This case is what makes
  the other six meaningful: without it, the suite would pass against a middleware that rejected
  every request unconditionally.

`tests/integration/conftest.py` is new and holds three shared fixtures: `async_client` (an
`httpx.AsyncClient` wired to the app over `ASGITransport`), `test_user` (persists a real user row
and deletes it afterwards), and `auth_token` (a valid JWT signed for that user by the app's own
`create_access_token`). Both async fixtures dispose the SQLAlchemy connection pool on entry,
because pytest-asyncio creates a fresh event loop per test while `core/database.py` holds a
module-level pool, so a pooled connection can otherwise outlive the loop that opened it.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

Both are ticked in the sense the assignment defines for a codebase with documented pre-existing
failures: my changes introduce no new ones. I recorded both gates before writing any code and
again afterwards, and the numbers are identical — `make check` reports 182 pre-existing ruff errors
and aborts at its lint stage both times, and `make test-unit` reports 53 failed / 375 passed both
times. None of those failures is in a file this branch touches, and `make test-unit` runs
`tests/unit` only, so it cannot be affected by tests added under `tests/integration/`. Scoped
`ruff` and `black` pass cleanly on both new files, and `make test-integration` reports 13 passed,
0 skipped.

**Draft PR feedback received from:** Joseph Gutierrez ---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No review arrived. I opened PR #601 against `ascherj/pathreview` on August 2 and it has been open
and marked ready for review ever since; as of August 6 it carries zero reviews and zero comments.
Maintainer review is not part of this cohort, so this was the expected outcome rather than a sign
the PR was overlooked.

**How you responded:**
There was nothing to respond to, so I left the PR open and ready for review rather than closing it,
and I re-checked it immediately before submitting this entry to confirm no feedback had landed in
the interim.

---

### Reflection

**What was harder than you expected?**
The scope. Issue #90 reads like four small tests, one per rejection path the issue names, and that
is exactly how I planned it in Week 8, four skipped stubs and a deliberate decision not to touch
the database. Once I started unpacking what those tests actually needed, that plan fell apart: a
suite made only of rejection cases would pass against a middleware that rejected every request,
valid credentials included, so it could not detect the failure it exists to catch. Fixing that
meant standing up Postgres, persisting a real user, and signing a real token which was the exact work 
I had scoped out. And it landed late in the week instead of at planning time. What surprised me is 
that none of the difficulty lived in the code; after twenty years in the field, converting the fixtures
to async and following that pattern through was routine. The hard part was that the true shape of
the job only became visible after I had already committed to a smaller one.

**What did you learn about working in a large codebase?**
That it is sometimes correct to put blinders on. `make check` reports 182 pre-existing ruff errors
on this repo and `make test-unit` reports 53 failures, and the pre-commit mypy hook fails with 44
more across seven files in `api/` and `core/` that I never touched. It only sees them because my
tests import `api.main`. I committed with `SKIP=mypy` so that ruff and black still ran, which is
not something I would ever do in a project of my own. In a codebase this size the pre-existing
problems will absorb exactly as much attention as you give them, and scoping tightly to the files
you actually own is what keeps that from swallowing the week. I found that genuinely hard: errors
feel wrong to me even when I know they are documented, expected, and not mine to fix.

**How did AI tools help — and where did they fall short?**
The most valuable thing AI did for me this module had almost nothing to do with writing code. I
have executive functioning problems, so I built my own tooling, like a kickoff skill and a
grader-simulation skill, that turns each week's rubric into a ledger of required exhibits and then
audits the graded artifact against that ledger before I submit. That scaffolding is the bedrock of
how I keep up. The engineering itself I can do on my own, but doing it on a deadline against a
specific spec is where I have historically lost whole projects. Where it fell short was judgment
about scope. The Week 8 plan to cover only the four rejection paths and skip the database was
written with AI assistance, and it was confidently wrong. Nothing in that conversation
flagged that a suite made entirely of rejection tests proves nothing about a middleware that
rejects everything. It is the one point in the module where I got genuinely angry at the tool. What
corrected it was reading the exits of `get_current_user` in `api/middleware/auth.py` myself. 

**What would you do differently if you started over?**
I would have pushed back immediately on the plan to avoid the database. I was optimizing for how
long the work would take rather than how well it would work, and that is exactly why it ran long.
The fixtures I skipped in Week 8 had to be written anyway in Week 9, under deadline, as
`tests/integration/conftest.py`. Scoping to save time is what cost me the time. The second thing I
would change came out of the feedback on my Week 9 submission, and I agree with it: my `test_user`
fixture writes a row to a shared dev database and removes it in teardown, so a run that dies
mid-test leaks a row that breaks the next run, where binding each test to a single connection and
rolling back a transaction would make cleanup impossible to skip. The related point is one I would
not have reached on my own. I treated the module-level connection pool in `core/database.py` as a
constraint to work around, disposing the pool on fixture entry so it could survive pytest-asyncio's
per-test event loop, when the fact that it made testing fragile was really signal about the
production code's coupling. Next time I want to read that kind of friction as information rather
than as an obstacle.

**What are you most proud of from this module?**
Completion. I have battled ADHD for half my life, and showing up ten weeks running through the lectures,
issue selection, `PLAN.md`, PR #601, and now this reflection, and finishing each one before its deadline
is not a small thing for me by any stretch of the word. The code was never the part in question, but 
being there to write it is the fight. I fought it and won, and I want to do it again.
