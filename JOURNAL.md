# Module 3 Journal — PathReview

My running record of Module 3 work. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report whether PostgreSQL, Redis, and the
vector DB are reachable, returning 200 when everything is up and 503 otherwise.
Its Redis probe in `api/routes/health.py` builds the client with
`redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`, but the
`Settings` class in `core/config.py` only defines Redis connection as a single
`redis_url` field — it has neither `redis_host` nor `redis_port`. So the very
first attribute access (`settings.redis_host`) raises `AttributeError`, which the
surrounding `try/except` swallows and records Redis as `"unhealthy"`, forcing the
whole endpoint to return HTTP 503 even when Redis is actually running. A
successful fix makes the probe read the config that actually exists — e.g.
building the client from `settings.redis_url` via `redis.Redis.from_url(...)` — so
the health check reflects Redis's true state and the endpoint returns 200 when all
dependencies are healthy. The change is contained to the `api` module (the health
route), with an accompanying unit test.

**Branch name:** `fix/155-health-check-redis-host-setting`

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?"

- **Scope is small and bounded.** The defect lives in one file (`api/routes/health.py`,
  the Redis-probe block around lines 44–46). The only other file involved is
  `core/config.py`, and only to read that `redis_url` already exists — no config
  changes are strictly required.
- **Root cause is already understood, not just suspected.** It's a concrete
  attribute mismatch: the route reads `settings.redis_host` / `settings.redis_port`,
  and `Settings` exposes `redis_url` instead. I confirmed this by reading both files,
  not by guessing.
- **Low blast radius.** The fix touches only the health route's Redis branch; it
  doesn't change the database or vector-DB probes, the response schema, or any other
  endpoint. No DB migration, no dependency changes, no frontend work.
- **Testable.** It can be covered by a small unit test that mocks the Redis client
  and asserts the probe uses the real config and reports `healthy` when the ping
  succeeds — matching the project's "every code change includes/updates tests" rule.
- **Fits a Tier 1 first contribution.** Clear, reproducible-by-reading, and
  self-contained. The main thing to watch in Weeks 8–9 is choosing between
  `redis.Redis.from_url(settings.redis_url)` (preferred — uses the existing field)
  versus adding explicit `redis_host`/`redis_port` settings; I'll justify the choice
  in the PR.

_AI assistance: I used an AI tool to help navigate the codebase (locate the health
route and the Settings definition via search) and to confirm my reading of the bug.
I verified the mismatch myself by reading `api/routes/health.py` and `core/config.py`._

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/issaouedraogo/pathreview/commit/635e58d3ace3d1fd911acb98f3c0ba6dd450989a

**Reproduction summary:**
I reproduced the bug three ways. (1) Runtime: `settings.redis_host` raises
`AttributeError: 'Settings' object has no attribute 'redis_host'` — `Settings`
only defines `redis_url`. (2) Static analysis: `mypy api/routes/health.py`
reports `"Settings" has no attribute "redis_host"` (and `redis_port`) at lines
45–46. (3) A new unit test, `tests/unit/test_health_route.py`, simulates a
reachable Redis (mocked `ping()` succeeds) and asserts the `/health` probe
reports Redis `"healthy"`; it fails today because the attribute access crashes
before the client is built, so it's marked `xfail(strict=True)`. Applying the
intended fix locally turned it green (the strict marker then flagged XPASS),
confirming the test pins the real defect.

**PLAN.md link:** https://github.com/issaouedraogo/pathreview/blob/fix/155-health-check-redis-host-setting/PLAN.md

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
- Choosing `redis.Redis.from_url(settings.redis_url, decode_responses=True)`
  (preferred — reuses the existing field) over adding `redis_host`/`redis_port`
  settings. Leaning toward `from_url`; will justify in the PR.
- The route uses a blocking sync Redis client inside an async handler. Out of
  scope for this issue, but I'll note it as a possible follow-up rather than
  expand the blast radius.

_AI assistance: I used an AI tool to help set up the local environment, write the
reproduction test, and draft this plan. I verified each reproduction path myself
(ran the failing test, ran mypy, and confirmed the fix flips the test green)._

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix. The `/health` Redis probe now builds its client with
`redis.Redis.from_url(settings.redis_url, decode_responses=True)` instead of the
nonexistent `settings.redis_host` / `settings.redis_port`
([api/routes/health.py](api/routes/health.py)). PLAN.md sub-tasks done: (1) rewrite
the probe, (2) keep the failure path intact, (3) flip the reproduction test into a
passing regression test, (4) add a negative-path test. Verified end to end against
live services: the Redis probe went from `unhealthy` (`'Settings' object has no
attribute 'redis_host'`) to `healthy`. Both unit tests in
[tests/unit/test_health_route.py](tests/unit/test_health_route.py) pass.

**Next steps:**
Open a draft PR early for peer/mentor feedback, fill in the PR template, and add
Check-in 2 with the PR link on Sunday.

**Blockers:**
None for #155. Noted: a live `/health` call still returns 503 because of a
*separate, pre-existing* bug in the Postgres probe (`db.execute("SELECT 1")` needs
`text("SELECT 1")` under SQLAlchemy 2.0). It is unrelated to #155, present before
my change, and out of scope — I'll document it in the PR.

---

### Check-in 2 (end of week)

**PR link:** _pending — will add once the PR is opened_

**Branch:** `fix/155-health-check-redis-host-setting`

**What you built:**
The `/health` endpoint's Redis probe now reads the Redis connection from the
`redis_url` setting that actually exists (via `redis.Redis.from_url(...)`), so it
reports Redis's true state instead of always crashing on a missing attribute and
reporting `unhealthy`.

**Tests added or updated:**
`tests/unit/test_health_route.py` — a happy-path test (reachable Redis → `healthy`
→ 200) and a failure-path test (unreachable Redis → `unhealthy` → 503).

**Self-review confirmation:** [ ] make check passes [ ] make test-unit passes
_(Codebase has documented pre-existing failures — see PR description. "Passes"
here means my change introduces no new failures: unit failures unchanged at 53,
ruff errors reduced 182 → 179, and two `redis_host`/`redis_port` mypy errors
removed.)_

**Draft PR feedback received from:** _pending_
