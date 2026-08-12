## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/70

**Issue title:** Add rate limiting per IP address in addition to per user

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, unauthenticated requests are not rate-limited at all. As it is, the current rate-limiter
found in safety/rate_limiter.py limits requests per authenticated user-id. Adding a rate limiter per IP-address as a secondary layer would cover the issue with unauthenticated requests. 
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

**Branch name:** feat/#70-rate-limiting-addition

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** (fill in after committing — will be the commit adding `tests/integration/test_rate_limiting_reproduction.py`)

**Reproduction summary:**
Confirmed `RateLimiter` in `safety/rate_limiter.py` is never wired into the app. No route or middleware calls `check_rate_limit`, so no request is throttled today. Reproduced two ways: (1) manually, ran the app locally against Dockerized Postgres/Redis and fired 150 rapid unauthenticated `curl` requests at `/`, all 150 returned `200` with zero `429`s; (2) added a failing integration test, `tests/integration/test_rate_limiting_reproduction.py`, which sends `rate_limit_per_minute + 20` unauthenticated requests through a `TestClient` and asserts a `429` appears — it currently fails, proving the gap exists at the point where `api/main.py` builds the middleware stack (no `RateLimitMiddleware` is registered, unlike `RequestIDMiddleware`).

**PLAN.md link:** [PLAN.md](./PLAN.md) (root of this fork; will update with the GitHub blob link once pushed)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Biggest open question is IP resolution behind a reverse proxy (`X-Forwarded-For` vs `request.client.host`) — no trusted-proxy config exists in this codebase yet, so I'm deferring that to a follow-up rather than trusting a spoofable header now. See Risks & Unknowns in PLAN.md for the full reasoning.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix per `PLAN.md`: added `RateLimitMiddleware` in `api/middleware/rate_limit.py` and wired it into `api/main.py` ahead of `CORSMiddleware`, so a 429 still gets CORS headers. It checks every request against an IP-based bucket and, when a valid JWT is present, an additional per-user bucket, reusing the existing `RateLimiter` in `safety/rate_limiter.py`. The Week 8 reproduction test (`tests/integration/test_rate_limiting_reproduction.py`) now passes. Added `tests/unit/test_rate_limit_middleware.py` with 5 tests covering IP-only requests, IP+user requests, either layer over its limit, and invalid-token fallback to anonymous. Both changes are committed on `feat/#70-rate-limiting-addition` and pushed to origin.

Before committing, re-verified the issue's premise against the actual code: grepped the whole codebase for any existing caller of `RateLimiter`/`check_rate_limit` outside `safety/` and found none — no request, authenticated or not, was ever throttled before this fix. That's why the middleware adds both layers rather than only the per-IP layer the issue title asked for; adding IP-only would have left the (also broken) per-user case unfixed.

Ran `make check`/`make test-unit` before and after: baseline had 53 pre-existing unit test failures and ~182 pre-existing lint errors unrelated to this issue; after the change, still exactly 53 failures (plus 5 new passing tests) and ruff/black/mypy are clean on every file touched — verified against the actual `pre-commit` hook directly, since its isolated mypy environment (only `mypy` + `types-redis` installed, no `fastapi`/`starlette`) type-checks differently than running mypy inside the full project venv.

**Next steps:**
Open a draft PR against `pathreview`, request peer/mentor review in Slack, and fill out the PR template — calling out the corrected root-cause understanding in the description. Address feedback, then finalize for Check-in 2.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** [#751 — Feat/#70 rate limiting addition](https://github.com/ascherj/pathreview/pull/751)

**Branch:** `feat/#70-rate-limiting-addition`

**What was built:**
Added `RateLimitMiddleware` (`api/middleware/rate_limit.py`), wired into `api/main.py` ahead of `CORSMiddleware`. It checks every request against an IP-based bucket and, when a valid JWT is present, an additional per-user bucket, reusing the existing `RateLimiter` in `safety/rate_limiter.py` — closing the gap where no request, authenticated or not, was ever throttled.

**Tests added or updated:**
`tests/unit/test_rate_limit_middleware.py` (new) — 5 tests against an isolated FastAPI app with only `RateLimitMiddleware` wired, mocking `RateLimiter.check_rate_limit`: IP over limit → 429 without calling the route; IP allowed, no auth header → route runs; IP allowed but user over limit → 429; both allowed → route runs; invalid token → falls back to IP-only. Also confirmed `tests/integration/test_rate_limiting_reproduction.py` (added Week 8) now passes.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
(Both pass in the sense the assignment defines for a codebase with documented pre-existing issues: `main` already has 53 pre-existing unit test failures and ~182 pre-existing lint errors unrelated to this issue, in files this PR doesn't touch. Verified before and after — counts are identical; this PR adds 5 new passing tests and zero new lint/type errors, confirmed against the actual `pre-commit` hook.)

**Draft PR feedback received from:** None yet — requested review in the class Slack channel, awaiting response.


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No comments or reviews landed on [#751](https://github.com/ascherj/pathreview/pull/751) by the Week 10 deadline — checked directly against the PR (`gh pr view 751`) rather than assuming from memory, and both the comments and reviews lists are empty. I posted in the class Slack channel back in Week 9 asking for a look but didn't get a response in time.

**How you responded:**
Since there was no feedback to respond to, I used the week to re-review my own PR with fresh eyes instead of leaving it idle. I re-read the diff end to end, re-ran `make check` and `make test-unit` against current `main` to confirm the pre-existing-failure counts I documented in Week 9 (53 unit failures, ~182 lint errors) hadn't drifted, and re-confirmed the middleware ordering rationale (before `CORSMiddleware`, so a 429 still carries CORS headers) still holds. No code changes were necessary — the PR still describes the header, but I'd take a substantive comment as a real prompt to revise, not just close out the assignment.

---

### Reflection

**What was harder than you expected?**
Establishing ground truth about the codebase's *existing* state was harder than actually writing the fix. Before I could trust that adding `RateLimitMiddleware` was correct, I had to grep for every caller of `RateLimiter`/`check_rate_limit` to confirm no request — authenticated or not — was ever being throttled. That single check in Week 9 changed the scope of the fix: the issue title only asked for per-IP limiting, but the per-user path was silently broken too, so an IP-only patch would have shipped a fix that looked complete but left half the bug in place. I underestimated how much of "solving an issue" in an existing codebase is actually verifying the issue's premise rather than trusting the title.

**What did you learn about working in a large codebase?**
The biggest difference from a solo project is that correctness isn't just "does my code do what I intended" — it's "does my code interact correctly with everything already there, including the parts that are already broken." I had to separate pre-existing failures (53 unit test failures, ~182 lint errors unrelated to my change) from anything I introduced, and prove that distinction with before/after counts rather than assert it. I also learned that tooling itself can lie about correctness in subtle ways — the `pre-commit` hook's isolated mypy environment (just `mypy` + `types-redis`, no `fastapi`/`starlette`) type-checked differently than running mypy inside the full project venv, so "it passes locally" and "it passes the actual gate that matters" turned out to be two different claims I had to check separately.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical, high-recall work: grepping across the codebase for every call site of a function, drafting the middleware skeleton against the existing `RequestIDMiddleware` pattern, and generating the initial spread of unit test cases (IP-only, IP+user, either layer over limit, invalid-token fallback) once I'd defined the behavior. It fell short on the judgment calls that actually mattered: deciding that the issue's stated scope (per-IP only) was insufficient once I found the per-user gap, deciding where in the middleware stack the rate limiter needed to sit relative to CORS so a 429 still carried the right headers, and deciding to explicitly defer the `X-Forwarded-For` trust question rather than quietly trusting a spoofable header. Those required reasoning about this specific production system's trust boundaries, not pattern-matching to a template.

**What would you do differently if you started over?**
I'd try to get eyes on the PR earlier than Week 9 — posting in Slack the same week I opened the draft rather than waiting until it was feature-complete, so there was more runway for a review cycle to actually close before the module ended. I'd also write the Week 8 reproduction test and the root-cause grep in the same sitting; I did the grep afterward almost by accident while re-verifying the issue, and it should have been step one of reproduction, not a gut-check I ran near the end.

**What are you most proud of from this module?**
Catching that the per-user rate limiting was also silently unwired before writing any fix code. It would have been easy to implement exactly what the issue title said, pass my own tests, and open a PR that technically closed the ticket while leaving a real gap in production. Slowing down to verify the premise instead of the request is the habit I most want to carry out of this module.
