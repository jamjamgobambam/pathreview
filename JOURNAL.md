# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/86

**Issue title:** Add an API rate limiting header (`X-RateLimit-Remaining`) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
There's already a `RateLimiter` in `safety/rate_limiter.py` that tracks how many requests each user/IP has made in a rolling window and knows exactly how many they have left but nobody's actually calling it. It's not hooked into any middleware, so none of that info ever reaches the client. Right now the only way to find out you're near your limit is to get slammed with a 429 out of nowhere. The fix is to actually plug that rate limiter into the request pipeline (next to `auth.py` and `request_id.py` in `api/middleware/`) and have it stamp `X-RateLimit-Limit` and `X-RateLimit-Remaining` on every response so clients can see it coming and back off on their own. I picked this issue because I've worked with APIs before, so I wanted something that would let me apply that background instead of starting from zero, but still push past a pure copy-paste fix.It also lines up well with what we've covered in class so far. 

**Branch name:** feat/86-rate-limit-headers

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [need to commit first](https://github.com/tanvi-g2/pathreview/commit/c80bda54d463dd2a08111b9cf441daf8b24a9015)

**Reproduction summary:**
Got the full stack running locally (Docker for postgres/redis/chroma, then `make run` for the API + frontend) and hit the root endpoint directly: `curl -i http://localhost:8000/`. The response comes back with `x-request-id` in the headers but there's no `x-ratelimit-limit` or `x-ratelimit-remaining` anywhere, on any request. Grepping the codebase confirms why: `RateLimiter.check_rate_limit` is only ever called from its own unit tests, never from `api/main.py` or anywhere in the actual request path. The class works, it's just not wired up to anything.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Blockers or open questions:**
Still need to figure out where a shared Redis client should live (there isn't one right now ,`health.py` just builds its own inline) and whether the sync `redis` client `RateLimiter` uses is going to be an issue inside an otherwise-async middleware. Details are in PLAN.md under Risks & unknowns.

**Pre-existing failures baseline (before starting Week 9 implementation):** ran `make check`/`make test-unit` before touching anything, `ruff` has 182 pre-existing errors (mostly in `agent/` and `rag/`), `mypy` aborts early on missing type stubs (`PyPDF2`, `jose`, `passlib`, `rank_bm25`) plus a numpy stub syntax issue, and `pytest tests/unit` has 53 pre-existing failures across unrelated modules (bias detector, PII scrubber, resume parser, etc.). None of this touches `api/`, `safety/rate_limiter.py`, or `core/config.py` ,`test_rate_limiter.py` is fully green. Recording this now so I can show later that my changes don't add to any of these counts.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are done. Added `core/redis.py` for a shared Redis client, built `RateLimitMiddleware` in `api/middleware/rate_limit.py` (identifies callers by user id or IP, calls the existing `RateLimiter`, stamps `X-RateLimit-Limit`/`X-RateLimit-Remaining` on every response, returns 429 once you're over), and wired it into `api/main.py` ahead of `RequestIDMiddleware` so a 429 still gets a request id attached. Verified it manually with curl, headers show up, and hammering the endpoint past 60 requests actually returns 429. Wrote 8 unit tests and 4 integration tests, all passing, and confirmed against my Week 8 baseline that I didn't introduce any new `ruff`/`mypy`/`pytest` failures.

**Next steps:**
Commit everything, open a draft PR, and peer revidw.

**Blockers:**
None right now.


### Check-in 2 (end of week)

**PR link:** TBD, opening draft PR next

**Branch:** feat/86-rate-limit-headers

**What you built:**
TBD

**Tests added or updated:**
TBD

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** TBD
