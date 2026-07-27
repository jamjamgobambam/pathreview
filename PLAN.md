## Solution plan

**Issue:** Add per-IP rate limiting as a secondary layer (#70)
https://github.com/ascherj/pathreview/issues/70

### Understand
The issue as written implies per-user rate limiting already exists and only
the IP-based secondary layer is missing. Investigation shows this isn't
accurate: no rate limiting exists anywhere in the live application. The
`RateLimiter` class (`safety/rate_limiter.py`) is fully built and unit
tested, and `rate_limit_per_minute` is configured in `core/config.py`, but
neither is imported or called anywhere in `api/`. `api/main.py` only
registers `CORSMiddleware` and `RequestIDMiddleware` — no rate-limiting
middleware or dependency exists. Confirmed via reproduction: 50 consecutive
requests to `POST /auth/login` with invalid credentials all return `401`,
with no `429` ever appearing, proving the endpoint (and by extension every
endpoint) is completely unthrottled. This is a real security gap on
`/auth/login` specifically, since it means no protection against
brute-force credential guessing.

The actual fix, then, is broader than "add IP as a secondary layer" — it's
wiring in rate limiting at all, designed from the start to support both
per-user (for authenticated requests) and per-IP (for unauthenticated
requests) identifiers, using the existing generic `RateLimiter` class as-is.

### Map
Files I expect to touch:
- `api/middleware/rate_limit.py` (new) — the rate-limiting dependency/middleware itself
- `api/main.py` — register the new middleware/dependency on the app
- `api/routes/auth.py` — apply rate limiting to `/auth/login` (and likely `/auth/register`)
- `core/config.py` — already has `rate_limit_per_minute`; may need a second setting for IP-based limits/window if they should differ from user-based limits
- `safety/rate_limiter.py` — no changes expected; `check_rate_limit` already accepts a generic identifier
- `tests/integration/test_auth_rate_limit.py` — update once the fix lands, to assert a `429` eventually appears instead of asserting its absence
- Possibly `tests/unit/` — new unit tests for the IP-extraction logic specifically

### Plan
1. Get a Redis client instance available to the middleware/dependency layer (check how `RateLimiter` gets instantiated in tests/unit for the expected pattern, and find/create the equivalent for the live app).
2. Build a rate-limit dependency (following the existing `get_current_user` dependency pattern in `api/middleware/auth.py`, since that's the idiomatic style already used in this codebase) that: checks if a request has an authenticated user (reuses `get_current_user` logic or catches its absence) and calls `check_rate_limit` with the user ID if so, or extracts the client IP and calls `check_rate_limit` with the IP if not.
3. Solve real-IP extraction correctly — check whether `request.client.host` is reliable in this Docker setup, or whether `X-Forwarded-For`/`X-Real-IP` headers need to be read instead (relevant since the app runs behind Docker's network).
4. Apply the dependency to `/auth/login` first (highest priority — the security-sensitive endpoint proven vulnerable in reproduction), then extend to other public endpoints as time allows within the estimated 4-6 hours.
5. Update the reproduction test to assert the new expected behavior (a `429` after N requests) instead of asserting rate limiting's absence, and add a companion test confirming legitimate traffic under the limit is unaffected.

### Inputs & outputs
**Input:** an incoming HTTP request (authenticated or not), plus configured limit/window values.
**Output:** either the request proceeds normally, or a `429 Too Many Requests` response is returned once the identifier (user ID or IP) exceeds the configured limit within the rolling window.

### Risks & unknowns
- Real client IP behind Docker/reverse proxy: `request.client.host` may return an internal Docker network IP rather than the real client IP; need to check for existing `X-Forwarded-For` handling elsewhere in the codebase (found none in `api/middleware/` currently) before deciding how to extract it.
- Shared IPs (NAT, office networks, school labs): an IP-based limit that's too strict could throttle multiple legitimate users behind the same IP. Need to pick a looser limit for IP-based checks than user-based ones.
- Redis availability: `check_rate_limit` already fails open on Redis errors (returns `True, limit`) — need to confirm this behavior is preserved and not accidentally changed when wiring in the new dependency.
- Whether to apply this as global middleware (every route) vs. a per-route dependency (opt-in per endpoint) — a global approach is more thorough but riskier to add late in a project with existing untested routes; a targeted per-route approach is safer given the 4-6 hour estimate, starting with `/auth/login`.
- Existing project-wide mypy failures (103 errors on `main`, unrelated to this issue) may make `make check` noisy; need to confirm my new code doesn't introduce additional errors beyond what's already present, since CI likely runs the same check.

### Edge cases
- Multiple legitimate users behind the same IP (NAT, shared office/school network) shouldn't get falsely throttled by an overly strict IP limit.
- A user who is authenticated should be limited by user ID, not additionally penalized by IP (avoid double-counting/double-throttling for the same actor).
- Redis being temporarily unreachable should fail open (allow the request) per existing behavior, not fail closed and lock everyone out.
- IP spoofing via forged `X-Forwarded-For` headers, if that's the extraction method used, should be considered even if not fully solved in this pass — worth a note for future hardening.
