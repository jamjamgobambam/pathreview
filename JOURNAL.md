# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report the status of the app's dependencies,
including Redis. To probe Redis, the handler in `api/routes/health.py` builds a client
from `settings.redis_host` and `settings.redis_port`. The problem is that the `Settings`
model in `core/config.py` never defines those fields — it only defines a single
`redis_url`. Because Pydantic settings don't expose attributes that weren't declared,
reading `settings.redis_host` raises an `AttributeError`, which crashes the Redis probe
before it can return anything. A successful fix makes `GET /health` complete without
error and report Redis as healthy/unhealthy — either by deriving host/port from the
existing `redis_url` (or adding the missing `redis_host`/`redis_port` fields) so the
handler and the config agree. This touches the API layer (`api/routes/health.py`) and
app configuration (`core/config.py`).

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" — scope & fit reasoning

- **Tier fit:** This is a Tier 1 / "good first issue" labeled `bug` + `api`. As my first
  contribution to a large, unfamiliar multi-service codebase, Tier 1 matches my comfort
  level — I want to learn the contribution workflow (fork → branch → PR → review) without
  fighting a sprawling change at the same time.
- **Scope is small and bounded:** The bug is a concrete mismatch between two files
  (`api/routes/health.py` reads `settings.redis_host`/`redis_port`; `core/config.py`
  defines only `redis_url`). I confirmed this myself with `grep redis core/config.py`.
  The fix is a handful of lines in one or two files — no cross-cutting refactor.
- **I can reason about the root cause:** It's an `AttributeError` from referencing
  Pydantic settings fields that were never declared. I understand exactly why it happens
  and what "fixed" looks like.
- **Testable without the full stack:** The failure is at the config/handler boundary, so
  I can exercise it and verify the fix with a focused test rather than needing the entire
  Docker + Redis environment stood up.
- **Not too trivial to explain:** Unlike a pure typo, it requires deciding *how* the two
  should agree (derive host/port from `redis_url` vs. add explicit fields), which gives me
  something real to reason about and write up.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Rrahul0414/pathreview/commit/5f8666c26fd88868b79573ca986195534757149a

**Reproduction summary:**
I added `tests/unit/test_health.py` and ran it locally with pytest. With the DB and Redis
both stubbed as reachable, `GET /health` still returned **HTTP 503** with `redis: "unhealthy"`,
and the captured log showed `redis_health_check_failed error="'Settings' object has no
attribute 'redis_host'"` — confirming the handler reads a `Settings` field that doesn't
exist. A second test confirms `settings.redis_url` exists while `settings.redis_host` /
`settings.redis_port` raise `AttributeError`. Result: `1 passed, 1 failed (expected)`.

**PLAN.md link:** https://github.com/Rrahul0414/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
Need to confirm `redis.Redis.from_url` on the pinned `redis>=5.0.0` accepts
`decode_responses=True` and preserves the db index / credentials from the URL — I'll verify
this while implementing the fix in Week 9. Docker isn't installed on my machine, so I
reproduced the bug with a stubbed unit test rather than a live stack; the fix and its tests
are fully verifiable this way, but I'll stand up Docker before opening the PR so I can smoke-test
`GET /health` end to end.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix from PLAN.md. Done so far: sub-task 2 (applied the fix in
`api/routes/health.py` — replaced the `redis.Redis(host=settings.redis_host, port=...)`
call with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`) and sub-task 3
(turned the Week 8 reproduction test green — the healthy path now returns 200 with
`redis: "healthy"`). Verified locally: `pytest tests/unit/test_health.py` shows the
healthy-path and root-cause tests passing.

**Next steps:**
Sub-task 4 — add the negative-path test (Redis unreachable → `redis: "unhealthy"` + 503).
Sub-task 5 — run the full local gate (`make check`, `make test-unit`), record the
pre-existing-failure baseline vs. my branch, fill in the PR template, and open the PR
against `ascherj/pathreview`.

**Blockers:**
The suite has many pre-existing failures from the other seeded issues, so I need to
establish a baseline to prove my change adds none. Also confirming `redis.Redis.from_url`
accepts `decode_responses=True` on the pinned `redis>=5.0.0` — confirmed it does.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/374

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
`GET /health` now builds its Redis client from `settings.redis_url` via
`redis.Redis.from_url(...)` instead of the nonexistent `settings.redis_host`/`redis_port`,
so the endpoint reports Redis status correctly (200/healthy when reachable, 503/unhealthy
when not) instead of always returning 503 with an `AttributeError` swallowed by the handler.

**Tests added or updated:**
Added `tests/unit/test_health.py` with three unit tests: (1) a regression guard that
`settings.redis_url` exists while `redis_host`/`redis_port` do not; (2) the healthy path —
GET /health returns 200 with `redis: "healthy"` and the client is built from `redis_url`
with `decode_responses=True`; (3) the unreachable path — a failing `ping()` yields
`redis: "unhealthy"` and HTTP 503. All three pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(Definition per the assignment: in this codebase with documented pre-existing failures,
"passes" = my changes introduce no new failures. Baseline on pristine `upstream/main`:
53 failed / 375 passed unit tests, ruff 161, mypy 106, black 52-to-reformat. On this
branch: 53 failed / 378 passed (my 3 new tests all pass), ruff 161, mypy 100 (−6), black 52.
Zero new failures introduced; 6 mypy errors removed.)_

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments arrived on [PR #374](https://github.com/ascherj/pathreview/pull/374).
As noted in the Summer 2026 course instructions, reviewer feedback isn't a feature this
term, so this is expected. The PR is still open, not a draft, and ready for review; as of
this entry it has 0 reviews and 0 comments.

**How you responded:**
No changes required — there was nothing to respond to. If feedback does come in later I'd
reply on the thread, make any warranted changes on the same `fix/155-health-check-redis-host`
branch, and document it here.

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't the fix — it was figuring out what "passing" even meant in this
repo. When I first ran `make test-unit` I got 53 failing tests, which was alarming until I
realized they came from the *other* seeded issues, not mine. I ended up checking out pristine
`upstream/main` and running the suite there to get a baseline (53 failed / 375 passed), then
comparing it to my branch (53 failed / 378 passed) to prove my change added zero new failures.
The bug itself was also sneakier than it looked: the `AttributeError` from `settings.redis_host`
was swallowed by a broad `except Exception` in `health.py`, so the visible symptom was just a
503 with "redis unhealthy" — nothing pointed at the config until I read the handler line by line.

**What did you learn about working in a large codebase?**
The biggest lesson was to match existing patterns instead of inventing my own. I had two ways
to fix #155: add `redis_host`/`redis_port` fields to `Settings`, or build the client from the
`redis_url` that already existed. I grepped for how Redis was used elsewhere and saw that
`rate_limiter.py`, `session_store.py`, and `market_analyzer.py` all receive an already-built
client and nothing else reads a host/port — so `redis_url` was clearly the single source of
truth, and `redis.Redis.from_url(...)` was the fix that kept it that way. I also learned to
keep the diff narrow: `health.py` had unrelated lint and mypy issues, but fixing them would
have muddied a one-line bug fix, so I left them and documented that they were pre-existing.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigation and rigor: tracing the mismatch between `health.py` and
`core/config.py`, grepping every `redis` usage, spinning up a minimal venv, and writing the
red→green reproduction test (`tests/unit/test_health.py`) plus the baseline comparison against
`upstream/main`. Where it fell short was anything requiring the live environment — Docker isn't
installed on my machine, so I couldn't stand up the stack or hit `localhost:8000/health` for
real, and I had to lean on stubbed unit tests instead. The genuinely judgment-heavy calls were
also mine: choosing `from_url` over new config fields, and deciding how much of the surrounding
mess to leave alone.

**What would you do differently if you started over?**
I'd install Docker up front so I could reproduce the 503 against a real running server and
smoke-test the fix end to end, rather than proving everything through mocked unit tests. I'd
also open the draft PR earlier in the week — I had the fix done well before I opened #374, and
opening sooner would have left room for peer feedback in Slack. On issue selection I'm happy I
stayed Tier 1, but I might have picked one with a runnable end-to-end path so the verification
story was less dependent on stubs.

**What are you most proud of from this module?**
The verification discipline around a tiny change. The actual fix is one line, but I backed it
with a reproduction test that failed on `main`, a negative-path test for an unreachable Redis,
and a measured baseline showing my branch introduced zero new failures and actually removed 6
mypy errors. Turning "I think this is fine" into "here are the numbers proving it's fine" — in
an unfamiliar codebase full of pre-existing breakage — is the thing I'd point to.
