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

**PR link:** https://github.com/ascherj/pathreview/pull/480 (draft)

**Branch:** feat/86-rate-limit-headers

**What you built:**
Wired the existing (previously unused) `RateLimiter` into the request pipeline as a new `RateLimitMiddleware`. It identifies each caller by user id or IP, stamps `X-RateLimit-Limit`/`X-RateLimit-Remaining` on every response, and returns a 429 once someone's over their limit, still with a request id attached.

**Tests added or updated:**
`tests/unit/test_rate_limit_middleware.py` (10 tests, mocked `RateLimiter`, covers identifier selection incl. expired/malformed tokens, and header/429/Retry-After behavior) and `tests/integration/test_rate_limit_headers.py` (4 tests against the real app + real Redis: headers present, remaining count decreases, 429 after 60 requests, `/health` excluded).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(with documented pre-existing exceptions — see the Week 8 baseline note and the PR description: `ruff`/`mypy`/`pytest` all have pre-existing failures unrelated to this change, confirmed via baseline runs and a `git stash` test before committing. My changes introduce zero new failures.)

**Draft PR feedback received from:** a reviewer on PR #480. Suggestions: a stronger comment protecting the middleware registration order, a test for expired (not just malformed) Bearer tokens, and a `Retry-After` header on 429s. Addressed all three in a follow-up commit.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
Got one round of review on the draft PR (#480). All three points were framed as optional polish, not blockers: (1) the middleware-ordering rationale in the PR description was clear but easy to accidentally break in a future refactor, so a comment right at the registration site would help protect it; (2) the description said the identifier falls back to IP on an invalid token, but it wasn't clear whether that also held for an *expired* token specifically, and whether a test already covered it; (3) since the 429 already carries rate-limit headers, a `Retry-After` header would be a natural addition for clients if the window length was readily available.

**How you responded:**
Addressed all three in a follow-up commit: strengthened the comments around `app.add_middleware(RateLimitMiddleware)`/`app.add_middleware(RequestIDMiddleware)` in `api/main.py` to explicitly say why the order matters and not to reorder them; added `test_expired_bearer_token_falls_back_to_ip` (the existing malformed-token test didn't specifically cover expiry); and added a `Retry-After` header (using the same rolling window as the rate limiter) to 429 responses, with a test confirming it's present on 429s and absent on 200s. Re-ran the full unit + integration suite after — no regressions, 2 new tests. Then marked the PR ready for review.

---

### Reflection

**What was harder than you expected?**
Setting up docker was quite a bit harder than i thought it would be, the instructions in  the module didnt quite cover everything so i ended up doing some external research on docker, what it's used for and how to set it up so I could get started on the project. 

**What did you learn about working in a large codebase?**
I learned how important it is to spend time familarizing yourself with the codebase and understanding teh conventions and guidelines for the project. it can make a huge difference in whether your pr gets accepted or not. A good example of this was when I found that health.py's Redis check was silently broken the whole time, it references settings.redis_host redis_port which don't even exist on the settings class, so it always fails and gets swallowed by a try/except. Nobody would catch that without actually reading through how the pieces connect. 

**How did AI tools help — and where did they fall short?**
They were very helpfull in famililarizing myself with the codebase, it was a bit overwhelimg at first but they were able to give a quick summary anf suggestions for how to trace through everything. Sometimes they would fall short in knowing how to best implement things and looking at the big picture and all the factors, which is where I came in. For example, when it came time to reproduce the issue, Claude wanted to jump straight to writing an automated failing test, but I just wanted to run the app myself and see the bug happen with my own eyes first, which honestly gave me a better sense of the problem. 

**What would you do differently if you started over?**
I would start planning earlier and give myself more time to actually implement the fixes. I turned in my planning assignments a bit later and then felt rushed with the implementation part of the project. 

**What are you most proud of from this module?**
I'm proud of making an open source contribution. I've always been scared and overwhlemed and never had the courage to contribute to open source projects, but now I feel much more comfortable with the process and would be much more likely to do so in the future. 