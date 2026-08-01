# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/70

**Issue title:** Add rate limiting per IP address in addition to per user

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview ships a Redis-backed rolling window `RateLimiter` in `safety/rate_limiter.py`, and the issue points out that limiting only happens per authenticated user ID, which leaves unauthenticated traffic to public endpoints with no limit at all. Someone hammering the health or auth routes without logging in never gets throttled, so the safety layer only protects against users the app already knows about. A successful fix adds per-IP limiting as a second layer, applied in `api/middleware/` alongside the existing auth and request ID middleware, so every request gets checked against an IP budget and authenticated requests additionally get checked against their user budget. Requests over either limit should get a 429 response, and the fail-open behavior on Redis errors that the current limiter has should stay the same so an outage in Redis never takes down the API.

**Branch name:** feat/70-per-ip-rate-limiting

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes ("Is this right for me?")

- Scope fits the estimate. The limiter logic already exists and takes any identifier string, so the work is a middleware in `api/middleware/` plus tests, which matches the 4 to 6 hour tier 2 estimate.
- I understand the code involved. `safety/rate_limiter.py` is about 60 lines using Redis sorted sets, it already has a unit test suite in `tests/unit/test_rate_limiter.py`, and `api/middleware/request_id.py` gives me a pattern to follow for the new middleware.
- It is testable. Unit tests can cover IP keying and the two-layer check, and an integration test can hit a public endpoint repeatedly and assert the 429.
- Risk is manageable. The main thing to get right is reading the client IP correctly behind a proxy (X-Forwarded-For handling) so the limit can't be trivially spoofed or accidentally applied to the proxy itself.
- One thing I noticed on a first read: grepping the repo shows nothing in `api/` ever calls `check_rate_limit`, and `core/config.py` has a `rate_limit_per_minute` setting that nothing reads. So the per-user limiting the issue describes may only exist as the unwired class, and my first task is confirming where enforcement actually happens today, since that decides whether I am adding a second key to existing middleware or building the middleware layer that applies both.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/MatthewOscar/pathreview/commit/49e0e52b260cbfe95f3a3225a07380d6b4690890

**Reproduction summary:**
With the app running locally I sent 80 rapid `POST /auth/login` attempts with wrong credentials from a single IP, and every request came back 401 with no 429 ever appearing. This confirmed the gap from my Week 7 read: `api/main.py` registers only CORS and request ID middleware, so the commit above adds a strict xfail test documenting that no rate limiting middleware exists in the request path.

**PLAN.md link:** https://github.com/MatthewOscar/pathreview/blob/feat/70-per-ip-rate-limiting/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
- The plan decodes the Bearer token inside the middleware to get the user identity, since `get_current_user` in `api/middleware/auth.py` is a route dependency and runs too late. I want to confirm in PR review that the maintainers are fine with that, and with `/health` staying exempt as a liveness probe.
- `check_rate_limit` returns a remaining request count, so the plan uses a fixed `Retry-After: 60`. If reviewers want the real seconds until reset, `RateLimiter` would need a small extension, which I have kept out of scope for now.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1 through 4 from PLAN.md are implemented: `RateLimitMiddleware` in `api/middleware/rate_limit.py` enforcing the `ip:` budget on every non-exempt request and the `user:` budget when a Bearer token decodes, IP extraction with the new `rate_limit_trust_proxy` opt-in, the full 429 contract, and the wiring in `api/main.py`. Thirteen unit tests pass against a mocked Redis client. Before touching code I recorded the repo baseline the course guide asks for: 182 ruff errors, 52 files black would reformat, 5 mypy stub errors plus 44 more reachable from `api.main`, and 53 failing unit tests, all pre-existing.

**Next steps:**
Promote the Week 8 xfail repro test into real assertions, verify the fix live against the running app, re-run the full check suite against the recorded baseline, and open the PR.

**Blockers:**
The pre-commit mypy hook fails on the pre-existing type errors whenever `api/main.py` changes, so that commit needed `--no-verify` with the identical before and after error set documented in the commit message.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/313

**Branch:** `feat/70-per-ip-rate-limiting`

**What you built:**
Middleware that applies the existing `RateLimiter` to the request path with two rolling-window budgets: per IP for all traffic and per user for authenticated traffic, returning 429 with `Retry-After` and `X-RateLimit` headers when either is exceeded. Redis runs off the event loop with short socket timeouts so a slow or dead Redis fails open instead of stalling the API. Verified live: 70 rapid unauthenticated login attempts got exactly the configured 60 served, then straight 429s, while `/health` stayed exempt.

**Tests added or updated:**
`tests/unit/test_rate_limit_middleware.py` (new, 13 tests): budgets and identifier keys, the 429 header and body contract, `/health` exemption, both `X-Forwarded-For` trust modes, token edge cases, zero limit, missing client, and fail-open on connection errors and timeouts. `tests/unit/test_ip_rate_limiting_repro.py` (promoted from the Week 8 xfail, 4 tests): middleware registered, the real stack constructs with the kwargs wired in `api/main.py`, a request flows with Redis unreachable, and CORS preflights keep `X-Request-ID`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(per the course definition for a codebase with documented pre-existing failures: both commands fail before and after my branch with byte-identical failure sets, so my changes introduce no new failures; every file I added or touched passes ruff, black, and mypy individually, and unit tests went from 375 to 392 passing)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
I checked PR #313 through the end of the week. There are no reviews or comments, and the PR still shows as awaiting review. This was expected, since reviewer feedback is not part of the Summer 2026 offering. The two questions I flagged for reviewers in Week 8, whether decoding the Bearer token inside the middleware is acceptable and whether `/health` should stay exempt, remain open on the PR for whenever a maintainer picks it up.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The state of the checks in the existing codebase. I expected the middleware logic to be the hard part, and it mostly went to plan. What I had not planned for was that `make check` and `make test-unit` already failed on main before I made any changes: 182 ruff errors, 52 files black wanted to reformat, dozens of mypy errors, and 53 failing unit tests. "Existing tests still pass" turns into an evidence problem at that point. I ended up recording the full failure set before my first commit and diffing it after each change to show nothing new appeared beyond my added tests. The pre-commit mypy hook made this concrete: any commit touching `api/main.py` was blocked by pre-existing type errors in files I never touched, so I had to commit with `--no-verify` and document the unchanged error counts in the commit message. I never got comfortable doing that, but it kept the diff reviewable.

**What did you learn about working in a large codebase?**
Issue descriptions describe the code the author remembers, so they have to be checked against the repo before planning anything. Issue #70 asked for per-IP limiting "in addition to per user," which implies per-user limiting exists. It existed only as an unwired class: nothing in the request path ever called `check_rate_limit`, and the `rate_limit_per_minute` setting had no readers. Grepping for callers during issue selection is what caught this, and it changed the work from "add a second key" to "build the enforcement layer." I also learned a kind of restraint I never need in my own projects. In my own code I fix lint errors as I find them; here, touching any of those 182 ruff errors would have buried my change in noise, so leaving known problems alone was part of doing the job well. Finally, framework mechanics I would have glossed over solo matter more when someone else has to trust the change: Starlette's `add_middleware` prepends, so registration order is the reverse of runtime order, and my wiring tests assert the built stack because of it.

**How did AI tools help — and where did they fall short?**
AI was most useful for mapping and for test breadth. It found the no-callers situation quickly, surfaced `api/middleware/request_id.py` as the house pattern to copy, and helped me enumerate a 13-test matrix for the middleware (trust-proxy modes, token edge cases, zero limit, missing client, timeout fail-open) that I would have partially missed on my own. It also caught a bug in review: the sync Redis client was being called directly in async `dispatch`, which would have stalled the event loop under a slow Redis. Where it fell short was anything requiring the running system or a judgment call. Confirming the fail-open behavior meant killing Redis and watching requests still succeed, and confirming enforcement meant sending 70 rapid login attempts and counting 60 served before the 429s started. And the scope questions, like whether `/health` deserves an exemption as a liveness probe, are maintainer decisions; the model will argue either side, so I made the call myself, documented it, and flagged it for review.

**What would you do differently if you started over?**
I would run the reproduction during Week 7 instead of waiting for Week 8. I suspected during selection that enforcement did not exist, since grep showed no callers, and I confirmed it a week later with the 80-request login test. That confirmation is what settled the scope, and having it a week earlier would have let me raise my two open design questions with the maintainer before implementation instead of baking my best guesses into an unreviewed PR. I would also reconsider the fixed `Retry-After: 60`. I kept the computed reset time out of scope to avoid extending `RateLimiter`, but I ended up deep in that class's behavior anyway for the fail-open tests, so the extension would have cost little and made the header honest.

**What are you most proud of?**
The arc of the reproduction test. In Week 8 it was a strict xfail documenting that no rate limiting middleware existed in the request path. In Week 9 I promoted it into four assertions that construct the middleware stack with the wiring from `api/main.py`. The file that documented the bug now guards the fix, and it fails if anyone unwires the middleware later. That before-and-after is the part of the contribution I would show someone first.
