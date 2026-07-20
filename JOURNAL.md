## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/70

**Issue title:** Add per-IP rate limiting as a secondary layer

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The current rate limiter (`safety/rate_limiter.py`) only limits requests
per authenticated user ID, so unauthenticated requests to public endpoints
have no rate limiting at all. The `RateLimiter` class itself already
supports this use case — `check_rate_limit` takes a generic `identifier`
string and doesn't distinguish between a user ID and an IP address so
the core fix isn't in the rate limiter itself. The real work is in
`api/middleware/`: finding where the per user check is currently wired
in (likely a FastAPI dependency, based on the existing `get_current_user`
pattern) and adding a parallel path that extracts the client IP and calls
`check_rate_limit` with it when a request has no authenticated user. Key
open questions I'll resolve during reproduction: where exactly the
per user check is called, whether the app needs to account for a reverse
proxy when reading the client IP (via `X-Forwarded-For`), and what
limit/window values make sense for IP based limiting versus the existing
per user values.

**Branch name:** feat/70-per-ip-rate-limiting

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger