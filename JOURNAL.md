## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/70

**Issue title:** Add rate limiting per IP address in addition to per user

**Tier:** [x] Tier 2

**Problem summary:**
The existing `RateLimiter` in `safety/rate_limiter.py` supports rate limiting by any identifier, but it's only ever invoked with an authenticated user's ID. Requests that don't carry a user identity — like calls to public/unauthenticated endpoints — currently pass through with no rate limiting at all, leaving them open to abuse. This issue adds per-IP rate limiting as a secondary layer, applied via middleware in `api/middleware/`, so every request is bounded by client IP regardless of authentication state. A successful fix means unauthenticated traffic is now capped per IP using the same rolling-window Redis-backed limiter already used for per-user limits.

**Branch name:** feat/70-per-ip-rate-limiting

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** __REPRO_COMMIT_URL__

**Reproduction summary:**
Against the baseline (`main`) request path I sent 65 unauthenticated `GET /` requests
and every one returned `200` with zero `429`s — confirming unauthenticated traffic is
not rate limited at all. Driving the existing `safety/rate_limiter.py` limiter directly
with an `ip:` identifier (limit 5) denied the 6th request, proving the machinery works
and only the per-IP wiring into the request path is missing.

**PLAN.md link:** https://github.com/aryan1fatemi/pathreview/blob/feat/70-per-ip-rate-limiting/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
Client-IP resolution behind a proxy/load balancer is the main open question — whether to
trust `X-Forwarded-For`, and how to avoid collapsing all clients behind one proxy into a
single bucket. Also undecided: whether to exempt `GET /health` from the per-IP limit.

### Reproduction details

Reproduced self-contained (no Docker), Python 3.11 venv with `fastapi`, `httpx`, `redis`,
`structlog`. Two observations plus static evidence:

1. **Static evidence (baseline gap).** On `main`,
   `git grep -n check_rate_limit -- ':!tests'` returns only the definition in
   `safety/rate_limiter.py` — no call sites under `api/`. The limiter is never invoked in
   the request path, so no endpoint (authenticated or not) is throttled.

2. **Dynamic — gap.** A FastAPI app mirroring `main`'s public `GET /` (no IP middleware),
   hit 65× via `TestClient`:
   ```
   Sent 65 unauthenticated GET / requests (limit would be 60/min).
     200 responses: 65
     429 responses: 0
     RESULT: GAP REPRODUCED — no request was ever throttled
   ```

3. **Dynamic — root cause.** The real `RateLimiter` (from `safety/rate_limiter.py`) keyed
   by `ip:203.0.113.7` with `limit=5`:
   ```
   req #1: allowed=True  remaining=4
   ...
   req #5: allowed=True  remaining=0
   req #6: allowed=False remaining=0
   RESULT: limiter denies at request #6 when keyed by IP
   ```
   The limiter enforces limits correctly per IP; the fix is purely to invoke it per request
   in `api/middleware/`.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ ] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
The environment plumbing, not the fix itself. Writing `IPRateLimitMiddleware` was
straightforward once I'd reproduced the gap, but getting `make check` and
`make test-unit` to actually run cleanly took longer than the code change. The
project's `.venv` had been created inside WSL (`/usr/bin/python3`), so calling it
from Git Bash on Windows just failed with "No such file or directory" until I
routed commands through `wsl.exe` instead. On top of that, the pre-commit `mypy`
hook checks any staged file — including `tests/` — while the Makefile's
`typecheck` target only points at `api/ core/ ingestion/ rag/ agent/ safety/`. My
new test file passed the Makefile check but failed at commit time with ten
"missing type annotation" errors I hadn't seen locally. Neither of these were
part of the actual bug; they were friction in getting my real change verified.

**What did you learn about working in a large codebase?**
The existing `RateLimiter` in `safety/rate_limiter.py` already did everything the
issue needed — rolling window, Redis-backed, identifier-agnostic — it just had
zero call sites under `api/`. In my own projects I'd probably have reached for a
new abstraction; here the right move was to add nothing to the core logic and
only wire up a thin middleware layer that reused it with an `ip:` prefix. Working
in someone else's production code means the first job is figuring out what
already exists and trusting it, not re-solving a problem that's already solved
one layer down. It also means conventions (branch naming, commit style, where
middleware lives, what the CI actually checks vs. what the Makefile checks) are
not negotiable the way they would be solo — I had to match what was already
there rather than pick my own style.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical, well-scoped parts: writing the
middleware test suite in the same style as the existing `test_rate_limiter.py`,
running the reproduction steps and lint/type/test commands, and quickly
diagnosing why `mypy` failed differently in pre-commit vs. the Makefile. It fell
short on anything that needed real judgment about the codebase's intent — for
example, whether to trust `X-Forwarded-For` behind a proxy, or whether health-
check endpoints should be exempted from the per-IP limit. Those are product
decisions with tradeoffs that depend on how this specific service is deployed,
and I documented them as open risks in `PLAN.md` rather than guessing at an
answer.

**What would you do differently if you started over?**
I'd verify the dev environment (venv, `make check`, `make test-unit`) end-to-end
in week 7 or 8, before writing any code, instead of discovering the WSL/Windows
mismatch and the mypy scope gap only when trying to commit in week 9. I'd also
have written the middleware test alongside the middleware itself rather than as
a separate pass afterward — it's the same amount of work, but doing it in one
pass would have caught the type-annotation gap before I'd already moved on
mentally to "done."

**What are you most proud of from this module?**
Resisting the urge to over-engineer the fix. It would have been easy to build a
more general "pluggable identifier strategy" for the rate limiter, or to add
proxy-aware IP extraction "while I was in there." Instead the change stayed to
exactly what issue #70 asked for — one middleware class, one registration line,
one test file — and every risk I chose not to address (proxy IPs, health-check
exemption, Redis fail-open) is written down in `PLAN.md` instead of silently
ignored or half-implemented.
