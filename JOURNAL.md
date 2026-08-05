## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/90

**Issue title:** Add integration tests for authentication edge cases

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The auth middleware only has tests for the happy path — a valid token. There are no tests covering what happens when someone sends an expired token, a malformed one, a token signed with the wrong secret, or no Authorization header at all. These are exactly the cases that matter for security, since real attackers won't be sending valid tokens. The fix is adding integration tests to the existing test_auth_middleware.py file that cover each of these four edge cases and confirm the middleware rejects them correctly.

**Branch name:** test/90-auth-middleware-edge-cases

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/R1sh1-11/pathreview/commit/681dca4

**Reproduction summary:**
Confirmed `tests/integration/test_auth_middleware.py` does not exist in the repo — the issue is a gap in test coverage, not a broken behavior. Added a new test file with 4 failing/pending integration tests that document exactly what's missing: expired token, malformed token, missing header, and wrong-secret token all need to return 401.

**PLAN.md link:** [https://github.com/R1sh1-11/pathreview/blob/test/90-auth-middleware-edge-cases/PLAN.md](https://github.com/R1sh1-11/pathreview/blob/test/90-auth-middleware-edge-cases/PLAN.md)

**Blockers or open questions:**
The test client may trigger the app lifespan and require Docker/Postgres to be running during test execution. Need to confirm whether tests need a live DB or if the DB dependency can be mocked out for pure auth middleware testing.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 4 sub-tasks from PLAN.md are done. The test file covers expired tokens, malformed tokens, missing Authorization header, and wrong-secret tokens, and all 4 pass locally. Also caught and fixed a bug in my own plan, PLAN.md originally pointed at `GET /profiles`, which does not exist, so I switched the tests to hit `GET /profiles/{profile_id}` instead since it uses the same auth dependency.

**Next steps:**
Get peer or mentor feedback on the draft PR in Slack, then address anything that comes up before marking it ready for review.

**Blockers:**
None right now.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/524

**Branch:** test/90-auth-middleware-edge-cases

**What you built:**
Added integration tests for the auth middleware covering the four edge cases it was missing: expired tokens, malformed tokens, missing Authorization header, and tokens signed with the wrong secret. All four now correctly return 401.

**Tests added or updated:**
tests/integration/test_auth_middleware.py, 4 new tests. Each one hits the protected GET /profiles/{profile_id} route with a differently broken token and asserts a 401 response.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none, could not locate the course Slack in time

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in. Per the course note, reviewer feedback wasn't a feature this summer cohort. I also wasn't able to locate the course Slack in time to get peer feedback on the draft PR before finalizing it.

**How you responded:**
N/A, no feedback arrived to respond to.

---

### Reflection

**What was harder than you expected?**
Getting the app running locally took way longer than actually writing the tests. I hit a bug where three different model files (profile.py, review.py, ingested_source.py) each defined the same database index twice, once inline with index=True and once again in __table_args__. Postgres refused to create the same index twice on every single startup, so the whole app crashed before I could even claim the issue. I had to trace through SQLAlchemy error output, find the exact duplicate lines with grep, and delete them one file at a time. On top of that, WSL, Docker permissions, git authentication with GitHub's token requirements, and npm/vite all broke in sequence. None of that was mentioned in SETUP.md, and I probably spent more hours untangling environment issues than writing the actual test code.

**What did you learn about working in a large codebase?**
You can't read a whole codebase before touching it, you have to trace one thread at a time. For issue #90, I started from the exact file the issue named, found it didn't exist yet, then worked backward to the middleware it was supposed to test (api/middleware/auth.py), then to the security functions it called (core/security.py), then to where that middleware was actually used in real routes. I also learned that assumptions in a plan can be wrong. My PLAN.md said to test GET /profiles, but that route doesn't exist, only POST, GET by id, PUT, and DELETE do. My first test run failed with a 405 instead of 401, which told me I was hitting the wrong endpoint entirely. I had to grep the actual router decorators to find a real protected route before the tests could work.

**How did AI tools help — and where did they fall short?**
AI was most useful for pattern recognition, spotting that the same index bug existed in three separate files once I found it in one, and for writing boilerplate test scaffolding (the async httpx client setup) that I would have had to look up from scratch otherwise. Where it fell short was that I noticed I was leaning on it to think for me rather than with me. I was pasting error logs and running whatever command came back without always understanding why first. Partway through the module I made a point of slowing down and asking more why questions instead of just copying commands, especially once I got into git auth and merge conflict resolution, since those are skills I'll need without AI in the room.

**What would you do differently if you started over?**
I'd read the SETUP.md troubleshooting section completely before touching anything, since most of my early environment pain (docker-compose vs docker compose syntax, the Windows port 5433 note, the .env copy step) was already documented there and I found it after the fact. I'd also run my tests immediately after writing them instead of writing all four fixtures and functions first, since the actual bug (wrong route) would have surfaced on the first test instead of after I thought I was basically done.

**What are you most proud of from this module?**
Finding and fixing the duplicate index bug before I could even start the assigned issue. It wasn't part of issue #90 at all, it was a completely separate problem blocking local setup for probably every student who forked the repo after that bug was introduced. Tracing three separate SQLAlchemy stack traces back to the same root cause across three different model files, without anyone telling me what was wrong, felt like the first real debugging I did this module that wasn't just following instructions.