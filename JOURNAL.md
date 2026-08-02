## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/86

**Issue title:** Add an API rate limiting header (`X-RateLimit-Remaining`) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now API clients get no advance warning about how close they are to the rate
limit — they only find out by being blocked with a 429. In fact, the project ships a
working `RateLimiter` class in `safety/rate_limiter.py`, but nothing in the request
path ever calls it, so no limit is actually enforced and no rate-limit information
reaches clients. The fix adds middleware in the `api/` layer (following the existing
`RequestIDMiddleware` pattern) that runs the limiter on each request and attaches
standard `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers to every response,
returning a 429 with those same headers when the limit is exceeded. A successful fix
means clients can read their remaining quota from any response and back off before
they ever hit a hard block.

**"Is this right for me?" — scope reasoning:**
Reasonable Tier 2 fit. The limiter logic already exists and is unit-tested, so the
core algorithm isn't the work — but this isn't purely cosmetic either: it means adding
new middleware to the live request path, deciding how to key the limit (client IP),
handling the 429-with-headers case, and reasoning about Redis failure/fail-open
behavior, which is more than a one-line change. The change stays contained to
`api/middleware/rate_limit.py`, `api/main.py`, and a new test file, and doesn't touch
the database, LLM, or frontend. The design decisions — enforce vs. headers-only and
which identity to key on — are already settled (enforce + client IP). Estimated effort
in the tracker is 3–5 hours, which matches a middleware-plus-tests task.

**Branch name:** `feat/86-ratelimit-headers`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/isomer04/pathreview/commit/ec0a927276011808879f5f6a021152a25ebb6f4c

**Reproduction summary:** I sent 65 in-process requests from the same test client to the dependency-free `/` API route, exceeding the configured 60-request limit. Every request returned `200`, the final response had no `X-RateLimit-Limit` or `X-RateLimit-Remaining` header, and `X-Request-ID` was present; separately, all 19 existing `RateLimiter` unit tests passed, confirming that the gap is missing API wiring rather than the limiter algorithm.

At the reproduction commit (`ec0a927276011808879f5f6a021152a25ebb6f4c`), I ran:

```powershell
.\.venv\Scripts\python.exe -c @'
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)
responses = [client.get('/') for _ in range(65)]
last = responses[-1]

print('request_count=', len(responses))
print('status_codes=', sorted({response.status_code for response in responses}))
print('429_count=', sum(response.status_code == 429 for response in responses))
print('X-RateLimit-Limit=', last.headers.get('X-RateLimit-Limit'))
print('X-RateLimit-Remaining=', last.headers.get('X-RateLimit-Remaining'))
print('X-Request-ID-present=', 'X-Request-ID' in last.headers)
'@
```

**PLAN.md link:** https://github.com/isomer04/pathreview/blob/feat/86-ratelimit-headers/PLAN.md

**Blockers or open questions:** Confirm whether trusted proxy configuration is available before using forwarded IP headers; otherwise use `request.client.host`. Middleware order and Redis fail-open header semantics need to be covered explicitly by the implementation tests.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented every code sub-task in `PLAN.md`: added the rate-limit middleware, connected it to the existing Redis-backed limiter, registered it in the API, exposed the headers through CORS, and added HTTP-level unit tests. The middleware uses `request.client.host`, enforces the configured per-minute limit, returns `429` after exhaustion, and adds quota headers to allowed, denied, and handled error responses.

**Next steps:**
Monitor CI and reviewer feedback, address any required changes, and keep the PR ready for final submission.

**Blockers:**
None currently.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/563

**Branch:** `feat/86-ratelimit-headers`

**What you built:**
Added API middleware that checks the existing Redis rolling-window limiter by client IP, reports `X-RateLimit-Limit` and `X-RateLimit-Remaining` on responses, and returns a JSON `429` when the quota is exhausted. Middleware ordering preserves request IDs and CORS headers on rejected requests, and the synchronous Redis call runs in a worker thread instead of blocking the async request loop.

**Tests added or updated:**
Added `tests/unit/test_rate_limit_middleware.py` with eight tests covering allowed responses, the last allowed and first denied requests, route short-circuiting, independent client IPs, missing client metadata, Redis fail-open semantics, handled route errors, and request-ID/CORS behavior on `429` responses. The focused rate-limit suite passes all 27 tests.

**Self-review confirmation:** [x] make check introduces no new failures  [x] make test-unit introduces no new failures

Pre-existing failures were recorded before implementation and compared afterward. Ruff reported 182 findings before and 181 afterward; Black reported 52 files needing formatting before and 51 afterward; the new middleware passes targeted Ruff, Black, and mypy checks. The full unit suite had 53 failures and 375 passes before the change; after adding all eight focused tests, the same 53 unrelated tests fail and the pass count increases to 383.

**Draft PR feedback received from:** none
