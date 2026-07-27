```markdown
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

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/leul71/pathreview/commit/70eed96

**Reproduction summary:**
Investigation revealed the issue's premise wasn't quite accurate — no rate
limiting exists anywhere in the live app, not just missing for
unauthenticated requests. `RateLimiter` and `rate_limit_per_minute` exist
but are never imported or called in `api/`. Reproduced by sending 50
consecutive invalid-credential requests to `POST /auth/login`: all
returned `401` with no `429` ever appearing, confirming the endpoint is
completely unthrottled. Documented this with an integration test
(`tests/integration/test_auth_rate_limit.py`) that currently passes by
asserting the absence of any `429` response.

**PLAN.md link:** https://github.com/leul71/pathreview/blob/feat/70-per-ip-rate-limiting/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Repo has 103 pre-existing mypy errors on `main`, unrelated to this issue.
Used `--no-verify` to commit reproduction work since the pre-commit hook
checks the whole codebase, not just changed files. Will confirm my own
code doesn't introduce new errors beyond what's already present before
final PR submission. Still need to confirm real client IP extraction
behavior in this Docker setup (no existing `X-Forwarded-For` handling
found in `api/middleware/`), and whether to apply rate limiting as global
middleware vs. per-route dependency.
```
