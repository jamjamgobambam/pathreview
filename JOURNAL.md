# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/86

**Issue title:** Add an API rate limiting header (`X-RateLimit-Remaining`) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The API already enforces a rolling-window rate limit through `safety/rate_limiter.py`,
but that logic isn't actually wired into any request path, and clients have no way to
know how close they are to the limit until a request suddenly returns a 429. This
issue asks for a middleware in `api/middleware/` that calls into the existing
`RateLimiter` on every request and attaches standard `X-RateLimit-Limit` and
`X-RateLimit-Remaining` headers to the response, following the same pattern as the
existing `RequestIDMiddleware`. A successful fix lets API clients proactively back off
before hitting the limit instead of discovering it via failed requests.

**Branch name:** feat/86-rate-limit-headers

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**Scope reasoning (Is this right for me? checklist):**
- The affected files (`api/middleware/`, `safety/rate_limiter.py`) were explicitly
  named in the issue, and the estimated effort (3-5 hours) matched what I found once
  I read the code: `RateLimiter.check_rate_limit` already returns `(allowed, remaining)`,
  so the missing piece is purely the middleware wiring, not new rate-limiting logic.
- There was a clear existing pattern to follow (`RequestIDMiddleware` in
  `api/middleware/request_id.py`), which de-risked the implementation approach.
- Several other cohort members had also commented interest on this issue; since the
  tracker doesn't formally assign issues, I claimed it via comment and proceeded,
  noting the possibility of an overlapping PR later in review.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [tests/manual/repro_issue_86.py](tests/manual/repro_issue_86.py)
(see commit "test: add reproduction script for issue #86" on this branch)

**Reproduction summary:**
Ran a standalone script (`tests/manual/repro_issue_86.py`) against a git worktree
checked out at `main` (before the fix), sending 5 requests to `GET /`. Every
response came back `200` with `X-RateLimit-Limit` and `X-RateLimit-Remaining` both
`None`, confirming `RateLimiter.check_rate_limit` is never invoked anywhere in the
API layer despite being fully implemented and unit-tested — the gap is purely
missing wiring, not missing logic.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
No local Redis instance to test enforcement end-to-end against a live server (only
verified via the existing `Mock()`-based unit test pattern and the fail-open path,
which triggers naturally when Redis is unreachable). Also open: whether IP-based
identifier keying (necessary since auth resolves after middleware runs) is
acceptable long-term, or whether rate limiting should eventually move to a
user-aware route dependency instead.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented `RateLimitMiddleware` in `api/middleware/rate_limit.py`, wired it into
`api/main.py` alongside the existing `RequestIDMiddleware`, and wrote unit tests
covering the main sub-tasks from PLAN.md.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md`, run `make check` and `make test-unit`,
and open the PR for peer/mentor feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/237

**Branch:** feat/86-rate-limit-headers

**What you built:**
Added `RateLimitMiddleware`, which wraps the existing `RateLimiter` from
`safety/rate_limiter.py` and runs on every request, keyed by client IP. It attaches
`X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to every response, and
returns a `429` with those same headers when the caller exceeds the configured
limit, matching the existing `RequestIDMiddleware` pattern.

**Tests added or updated:**
Added `tests/unit/test_rate_limit_middleware.py`, covering: headers present on
success, remaining count reflects the limiter's output, `429` + headers returned
when the limit is exceeded, and remaining never goes negative.

**Self-review confirmation:** [x] make check passes*  [x] make test-unit passes*

*Both commands surface pre-existing issues on `main`, unrelated to this change —
confirmed identical before my changes by running both against `origin/main`:
- `make test-unit`: 53 pre-existing failures (`test_bias_detector.py`,
  `test_pii_scrubber.py`, `test_review_service.py`, `test_resume_parser.py`,
  etc.). My branch introduces zero new failures and adds 4 net new passing
  tests — this PR's own `test_rate_limit_middleware.py` and `test_rate_limiter.py`
  tests all pass.
- `make check`: 181 pre-existing ruff errors and 51 files needing `black`
  reformatting codebase-wide (182/51 on `main` — not worse). `mypy` fails to
  complete due to missing type stubs (`PyPDF2`, `jose`, `passlib`) and a
  numpy/Python-version stub mismatch, identical on `main`. Zero lint, format,
  or typecheck issues in the files this PR touches
  (`api/middleware/rate_limit.py`, `api/main.py`,
  `tests/unit/test_rate_limit_middleware.py`).

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

**Review feedback received:**
As of this writing, [PR #237](https://github.com/ascherj/pathreview/pull/237) has
received no reviewer comments and no requested changes — `gh pr view` shows zero
reviews and zero comments. I checked the cohort Slack channel and did not get a
peer or mentor review either, despite the PR being open and marked ready for
review since Week 9. Per the course guidance, I'm noting this and moving on
rather than blocking on it; there's nothing to respond to, so this week's actual
work is the reflection below.

**Responses to feedback:**
N/A — no feedback arrived to respond to. If a review comes in after submission,
I'll add a follow-up commit and note the exchange here rather than silently
resolving it.

**Reflection:**

*What I built and why.* I picked [issue #86](https://github.com/ascherj/pathreview/issues/86)
because it was scoped tightly enough to fit the time box, but not trivial: the
rate-limiting *logic* already existed and was already unit-tested in
`safety/rate_limiter.py` — the actual gap was that nothing in the request path
ever called it. That's a more honest bug to fix than it sounds, because the
easy failure mode is to assume "no rate limiting" means "write a rate limiter,"
when the real task was reading the existing code carefully enough to realize
the missing piece was wiring, not logic. I built `RateLimitMiddleware` to mirror
the existing `RequestIDMiddleware` pattern deliberately, rather than inventing a
new middleware shape — matching an established convention was more valuable
here than any cleverness on my part would have been.

*What went wrong, and how I responded.* Two things surfaced along the way that I
didn't fully appreciate at the start:

1. I couldn't test against a live Redis instance locally, so my verification
   leaned entirely on the existing `Mock()`-based unit test pattern and the
   fail-open path (which triggers naturally when Redis is unreachable, so it
   was actually exercised, just not by design). I flagged this as an open
   question in Week 8 instead of pretending it was fully verified — in
   retrospect I'd still make that call, but I'd also spend 20 minutes spinning
   up a local Redis container so the fail-*closed* path got real coverage too,
   not just fail-open.
2. When I ran `make check` and `make test-unit` for real (rather than trusting
   the checkboxes I'd initially filled in from memory), I found the codebase
   already has 53 failing unit tests and 181+ lint errors on `main`, unrelated
   to my change. My first draft of Check-in 2 just checked the boxes without
   saying that — which was wrong, even though my actual code was fine. The fix
   wasn't to lower the bar, it was to verify against `main` and document the
   difference explicitly, which is what the assignment's pre-existing-failures
   policy is actually asking for. That was a good, if slightly embarrassing,
   lesson in not trusting my own self-review without rerunning the commands.

*What I'd do differently with full context now.* Two things stand out:

- I'd open the PR earlier in Week 9 and post it in the cohort Slack channel the
  same day, rather than treating "draft PR feedback" as a checkbox to fill in
  later. No feedback arrived this cycle, and part of that is on me for not
  actively pinging someone rather than waiting for review to happen passively.
- I'd reconsider the identifier-keying decision (client IP, since auth resolves
  after the middleware runs) earlier and more deliberately. It works and is
  documented as a known tradeoff in the PR's "Notes for Reviewers," but if this
  were a real production system I'd want to decide up front whether IP-keyed
  limits are acceptable long-term (e.g., behind a shared NAT/proxy) or whether
  the middleware should sit after auth and key on user ID instead. I noted the
  tradeoff rather than resolving it, which was the right scope call for a
  3–5 hour issue, but it's the first thing I'd revisit with more time.

*What this taught me about review culture.* Getting zero feedback is its own
kind of data point: it means either the PR was clear enough that there was
nothing to push back on, or that asynchronous review only works if someone
actively drives it rather than assuming it happens automatically once a PR is
open. I'm treating it as the latter — the lesson isn't "my PR was flawless,"
it's "open PRs don't get reviewed by default; reviews get requested."
