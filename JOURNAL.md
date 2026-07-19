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
