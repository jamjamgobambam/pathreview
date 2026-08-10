## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [ X ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint (`api/routes/health.py`) checks Redis by building a client
with `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`. But the
`Settings` class in `core/config.py` never defines `redis_host` or `redis_port` — it
exposes a single `redis_url` instead. So the attribute lookup raises
`AttributeError: 'Settings' object has no attribute 'redis_host'` before a connection
is ever attempted. The surrounding `try/except` swallows that error, marks Redis
`"unhealthy"`, and the endpoint returns 503 regardless of whether Redis is actually
up — which defeats the point of a health check. A successful fix rebuilds the client
from the attribute that actually exists (`redis.Redis.from_url(settings.redis_url,
...)`), so `/health` reports Redis's real state instead of failing on a bad config
reference.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?" checklist reasoning

- **Scope is bounded and understood.** The bug lives in one function in one file
  (`api/routes/health.py`). I traced it end to end with the VS Code debugger: sent a
  `GET /health`, hit a breakpoint in the Redis block, and read the caught exception
  in Locals — `AttributeError("'Settings' object has no attribute 'redis_host'")`.
  I can explain both the cause (attribute doesn't exist) and the effect (`except`
  swallows it, so the endpoint always returns 503).
- **The fix is small and low-risk.** Replace the `host=/port=` construction with
  `redis.Redis.from_url(settings.redis_url, ...)`, matching the attribute the
  `Settings` class already exposes. No schema, migration, or API-contract change.
- **I can verify it.** I have the backend running locally and a saved request that
  reproduces the 503, so I can confirm the Redis dependency flips to `"healthy"`
  (with Redis up) once the fix lands.
- **Out of scope, deliberately.** While reproducing this I noticed `/health` also
  reports Postgres unhealthy — but for a different reason (`db.execute("SELECT 1")`
  needs SQLAlchemy's `text()` wrapper). That is not issue #155. I'm leaving it
  untouched to keep this branch to one intent; it belongs in its own issue/PR.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [`5b12f9f`](https://github.com/tmayush/pathreview/commit/5b12f9f). The added `tests/unit/test_health.py` encodes the reproduction. `test_health_check_does_not_reference_redis_host` asserts that `settings` has no `redis_host` or `redis_port`, and before the fix the Redis block reported `"unhealthy"` because the attribute lookup raised `AttributeError`.

**Reproduction summary:**
I ran the backend and sent `GET /health` with a VS Code breakpoint in the Redis block. The caught exception was `AttributeError("'Settings' object has no attribute 'redis_host'")`. It fired before any connection was attempted, the `except` swallowed it, and the endpoint returned 503 with Redis marked `"unhealthy"` even though Redis was up.

**PLAN.md link:** [PLAN.md](https://github.com/tmayush/pathreview/blob/fix/155-health-check-redis-host/PLAN.md)

**Walkthrough video (recommended):** not recorded.

**Blockers or open questions:**
None. The fix is a bounded, one-function change. The only care needed is keeping it separate from the codebase's documented pre-existing test and lint failures.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `api/routes/health.py` (sub-task 1). The Redis client is now built with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`. Added `tests/unit/test_health.py` (sub-task 2) with three passing tests.

**Next steps:**
Run the full `make check` / `make test-unit` baseline comparison (sub-task 3), finalize the journal, and open the PR (sub-task 4).

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/670

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
The `/health` endpoint built its Redis client from `settings.redis_host` and `settings.redis_port`. Those attributes don't exist on `Settings`, so the lookup raised `AttributeError`. The `except` swallowed it, Redis was always reported unhealthy, and `/health` returned 503 even when Redis was up. The fix builds the client from `settings.redis_url`, which does exist, using `redis.Redis.from_url`, so the check reports Redis's real state.

**Tests added or updated:**
Added `tests/unit/test_health.py`, the project's first tests for the health endpoint. They cover three cases: Redis reported healthy on a successful ping, Redis reported unhealthy (503) on a real connection failure, and a regression guard that fails if the client is ever built from `redis_host` or `redis_port` again instead of `redis_url`.

**Self-review confirmation:** [ X ] make check passes  [ X ] make test-unit passes

_Pre-existing failures note:_ On the base commit (`main`), `make test-unit` reports **53 failing tests** (for example `test_tech_detector`, `test_skill_extractor`, `test_structural_chunker`) and `make check` reports pre-existing lint and type errors. None of them relate to issue #155. After my changes the count is unchanged: the same 53 failures plus my 3 new passing tests. My change introduces no new failures. My new test file passes lint cleanly, and the 4 lint hits in `health.py` are pre-existing in-function imports that appear identically on `main`. So "passes" here means my changes introduce no new failures.

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [ X ] No — still awaiting review

**Summary of feedback:**
No review has come in yet. At the Week 10 deadline, PR [#670](https://github.com/ascherj/pathreview/pull/670) is open with status `REVIEW_REQUIRED` and has no reviews or comments from maintainers. It isn't a draft and the template is filled in, so it's ready whenever a maintainer picks it up.

**How you responded:**
There's nothing to respond to yet. If feedback shows up after the deadline I'll answer it on the PR. The most likely follow-ups I can think of are adding a short module docstring to `tests/unit/test_health.py` if someone asks, or opening a separate issue for the Postgres `text()` bug I flagged if a maintainer wants it fixed. I kept the PR to one change on purpose so it stays easy to review.

---

### Reflection

**What was harder than you expected?**
The fix was three lines. Proving it was clean took longer than writing it. `make test-unit` came back with 53 failures and `make check` printed a wall of lint and type errors, none of it mine. To claim my change was safe I had to check out `main`, record a baseline (53 failing, 375 passing), then confirm my branch produced the same 53 plus my 3 new passing tests. Without that baseline I'd have had no honest way to say I hadn't broken anything, and it would have been easy to see red output and assume I had. A smaller surprise: `pytest` wasn't installed in the venv at all, so the Makefile's test command pointed at a binary that didn't exist until I ran `uv pip install -e ".[dev]"`.

**What did you learn about working in a large codebase?**
That "passing" means something different in code you didn't write. In my own projects, green means green. Here the honest bar was "don't make it worse." I only had to avoid adding new failures, not repair a codebase I hadn't broken. I also learned to hold scope. While reproducing #155 I found a second real bug: the Postgres check in `/health` calls `db.execute("SELECT 1")` without SQLAlchemy's `text()` wrapper. The right move was to write it down and leave it for its own issue, not fold it into this PR. Tracing the original bug also meant reading files I'd never touch in my own work, following `settings.redis_host` back to `core/config.py` to confirm the attribute genuinely wasn't there instead of taking the error message on faith.

**How did AI tools help — and where did they fall short?**
AI was best at getting around the codebase and setting up scaffolding. It found every `redis` reference across `api/`, `safety/`, and `agent/` fast, pointed me at the existing `Mock()` Redis pattern in `test_rate_limiter.py` so my test matched the house style, and drafted both the `from_url` fix and the `TestClient` plus `dependency_overrides` harness. It was weaker on judgment. Deciding what belonged in scope, and reading the pre-existing failures for what they were, came down to me. The tool could run the commands, but I had to decide those 53 failures weren't mine to fix and that saying so plainly in the PR was the right call. It also couldn't push for me. My SSH key has a passphrase, so every push was a manual step I ran myself.

**What would you do differently if you started over?**
I'd take the `make check` and `make test-unit` baseline in Week 8 while reproducing, not in Week 9 while coding. Having the failure count in hand from the start would have killed the "did I break this?" doubt the first time I ran the suite. I'd also open the PR as a draft earlier in the week. I went straight to ready-for-review close to the deadline and left almost no room for peer feedback.

**What are you most proud of from this module?**
Not the three-line fix. The honesty around it. The `/health` endpoint had never had a single test, and my PR adds the first ones, including a guard that breaks the build if anyone puts the `redis_host` or `redis_port` reference back. And I wrote the pre-existing failures into the PR openly instead of quietly ticking every checkbox. That's the kind of PR I'd want to get if I were the maintainer.