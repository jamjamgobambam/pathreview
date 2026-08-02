## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/70](https://github.com/ascherj/pathreview/issues/70)

**Issue title:** Add rate limiting per IP address in addition to per user

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

The project as is only limits user request based on their authenticated user ID, but unauthenticated requests (e.g., to public endpoints) are not rate limited at all. The goal is to add in the IP limiter as an additional check within the rate limiter component as a secondary layer. If all things are implemented correctly, the project will automatically deny further requests from any users within the same IP if the limit has been reached.

**Branch name:** feat/70-rate-limit-per-ip

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Is this right for me?**: Yes

- Part 1: I understand the issue at hand, what the fix looks like, and knows where to pin point directly to add in the IP rate limiter.
- Part 2: Since I'm not a stranger to making pull requests, I can work with a Tier 2 issue involving communication between layers.
- Part 3: I managed to locate the appropriate code, where I think my changes will take place as well as the associated test file.
- Part 4: There are only 2 other people claiming this issue from other sessions, so I'm fine with it. I should have the time to do it within the upcoming weeks. This requested changes does not rely on anything else, so I can work on it right away.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/CherryQuartzio/pathreview/commit/a3a8a9bab7762b79a03144ef742925442465035b](https://github.com/CherryQuartzio/pathreview/commit/a3a8a9bab7762b79a03144ef742925442465035b)

**Reproduction summary:**
I added a test `test_reproduce_ip_rate_limit_gap` in `tests/unit/test_rate_limiter.py` that simulates 10 requests from the same IP address but with 10 different user IDs. Because `check_rate_limit` only checks the provided identifier, all 10 requests are allowed, reproducing the issue where an IP can bypass the limit by varying user IDs (or when unauthenticated).

**PLAN.md link:** [https://github.com/cherryquartzio/pathreview/blob/feat/70-rate-limit-per-ip/PLAN.md](https://github.com/cherryquartzio/pathreview/blob/feat/70-rate-limit-per-ip/PLAN.md)

**Walkthrough video (recommended):** [N/A]

**Blockers or open questions:**
No blockers. The next step is to update the signature of `check_rate_limit` to accept and check against `ip_address` in addition to the primary identifier.

JOURNAL.md Template: Week 9
Add this section below your Week 8 entry in JOURNAL.md. Fill in both check-ins — the first by Wednesday, the second by Sunday alongside your PR link.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented dual IP + user rate limiting in `safety/rate_limiter.py` (`check_rate_limit` now takes keyword-only `ip_address`, checks IP first then optional identifier, records both via a Redis pipeline). Added `api/middleware/rate_limit.py` and registered it in `api/main.py` so live requests are limited (429 when exceeded; `/health` and OpenAPI paths exempt). Updated `tests/unit/test_rate_limiter.py` (including `test_reproduce_ip_rate_limit_gap`) and added `tests/unit/test_rate_limit_middleware.py` — 35 related unit tests passing.

**Next steps:**
Open the draft PR, run full `make check` / `make test-unit` self-review against contribution standards, and fill Check-in 2 with the PR link.

**Blockers:**
None. Pre-existing unrelated `make test-unit` failures (53) and ruff lint noise in other modules remain; our rate-limit changes do not affect them.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/412

**Branch:** feat/70-rate-limit-per-ip

**What you built:**
`RateLimiter.check_rate_limit` now requires an `ip_address` and checks the IP bucket before the optional user identifier, recording both in Redis only when allowed (IP-only when unauthenticated). `RateLimitMiddleware` enforces that on API requests using the client IP and optional JWT `sub`, returning 429 when over the limit while exempting health and OpenAPI paths.

**Tests added or updated:**
`tests/unit/test_rate_limiter.py` — updated all call sites for `ip_address`, added the IP-gap reproduction case plus dual-bucket / unauthenticated / remaining-min cases. `tests/unit/test_rate_limit_middleware.py` — allow/429, IP extraction, optional JWT user id, and exempt paths (35 related tests passing).

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
- There are 53 pre-existing unit failures and unrelated ruff noise.
- **No new failures for new features of this branch.** `test_rate_limit_middleware.py` pass 100%.

**Draft PR feedback received from:** none
