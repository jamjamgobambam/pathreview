# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/86

**Issue title:** Add an API rate limiting header (`X-RateLimit-Remaining`) to responses

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
There's already a `RateLimiter` in `safety/rate_limiter.py` that tracks how many requests each user/IP has made in a rolling window and knows exactly how many they have left — but nobody's actually calling it. It's not hooked into any middleware, so none of that info ever reaches the client. Right now the only way to find out you're near your limit is to get slammed with a 429 out of nowhere. The fix is to actually plug that rate limiter into the request pipeline (next to `auth.py` and `request_id.py` in `api/middleware/`) and have it stamp `X-RateLimit-Limit` and `X-RateLimit-Remaining` on every response so clients can see it coming and back off on their own.

**Branch name:** feat/86-rate-limit-headers

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
