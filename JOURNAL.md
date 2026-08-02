## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/70](https://github.com/ascherj/pathreview/issues/70)

**Issue title:** [Add rate limiting per IP address in addition to per user #70]

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Currently unauthenticated/public API requests are not rate limited at all. The current rate limiter limits requests only for authenticated user ids. This results in vulnerabilities against attacks. To fix this we add a per ip address rate limiter.
relevant files: 
- safety/rate_limiter.py
- api/middleware/

**Branch name:** feat/70-ip-rate-limit

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
Starting up the app and using as many possible functions as possible.

**PLAN.md link:** [PLAN.md]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Confirmed via code review that `RateLimiter` (safety/rate_limiter.py) was never wired into the API at all — not for users, not for IPs. All 3 plan steps done: created `api/middleware/rate_limit.py` (`RateLimitMiddleware`), initialized a Redis-backed `RateLimiter` and registered the middleware in `api/main.py`, and added `ip_rate_limit_per_minute` alongside the existing `rate_limit_per_minute` in `core/config.py`.

**Next steps:**
implementation, tests, and lint.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `feat/70-ip-rate-limit`

**What you built:**
Added `RateLimitMiddleware` to enforce rate limits on all incoming requests before they reach any route, applying a per-IP limit to every request and an additional per-user limit for authenticated requests with valid bearer tokens. This closes the gap where unauthenticated traffic was previously unprotected. The middleware excludes `/` and `/health`, and returns a 429 response with a `Retry-After` header when limits are exceeded. The existing `safety/rate_limiter.py` remains unchanged because it provides the framework-agnostic Redis rate-limiting mechanism, while the new `api/middleware/rate_limit.py` handles FastAPI-specific request integration, keeping responsibilities cleanly separated.

**Tests added or updated:**
`tests/unit/test_rate_limit_middleware.py` covers: unauthenticated requests checked against the IP limit, 429 + `Retry-After` when the IP limit is exceeded, authenticated requests checked against both IP and user limits, 429 when only the user limit is exceeded, invalid/malformed tokens falling back to IP-only (no crash), and excluded paths skipping rate limiting entirely.

Mixing HTTP/FastAPI-specific logic into the generic Redis utility would couple it to the web framework unnecessarily. `safety/` already holds other framework-agnostic modules (e.g. `monitoring.py`), while `api/middleware/` is where the other request-handling glue lives (`request_id.py`, `auth.py`) — so the split follows the existing convention: `safety/` = policy/mechanism, `api/middleware/` = how it's wired into requests.

**Self-review confirmation:** [X] make check passes (on touched files — repo-wide `make check` has pre-existing, unrelated lint/test failures) [X] make test-unit passes (on touched files — same pre-existing unrelated failures elsewhere in the suite)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [X] Yes  [ ] No — still awaiting review
- By ChatGPT
**Summary of feedback:**
PR is well-scoped, focused change that introduces per-IP rate limiting before authentication, with appropriate tests and documentation. However, some concerns regarding the duplicate rate limiter, verify the middleware ordering is intentional and documented, ensure client IP extraction is secure, and to confirm that limits and related behavior is configurable instead of being hardcoded. Finally to simplify the known issues section so reviewers can quickly understand the current repository state. 

**How you responded:**
Not yet addressed in code — still pending. Plan is to: (1) clarify in docs/comments why `safety/rate_limiter.py` and `api/middleware/rate_limit.py` aren't duplicates (mechanism vs. wiring, per the split noted in Week 9), (2) document the middleware ordering rationale in `api/main.py`, (3) review the client IP extraction logic (e.g. trusting `X-Forwarded-For` only from a configured trusted proxy) to avoid spoofing, (4) move the hardcoded limits into `core/config.py` settings if not already fully covered by `ip_rate_limit_per_minute`/`rate_limit_per_minute`, and (5) trim the known issues section for clarity.

---

### Reflection

**What was harder than you expected?**
Knowing how to add to the existing repo without making changes that would conflict with other componenets unrelated to the issue.

**What did you learn about working in a large codebase?**
You don't understand or know every component that exists in the system and you don't necessarily need to. Its more important to grasp the surface level design and only understand the components you are working on and the components it affects.

**How did AI tools help — and where did they fall short?**
AI was really useful is pointing out what direction to go in for how to solve the problem and what topics to research in.

**What would you do differently if you started over?**
I would definitely change my planning so that I could be more efficient in focusing on how to solve my issue and how to tackle making changes to existing components vs making new components.

**What are you most proud of from this module?**
Fixing the issue and writing tests and documentation, it gave me the experience of working on a real repo.