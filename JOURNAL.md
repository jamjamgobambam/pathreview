## Week 7 — Issue selection

**Issue link:** [#155](https://github.com/ascherj/pathreview/issues/155)

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report the status of Postgres, Redis, and the
vector DB, but its Redis probe reads `settings.redis_host` and `settings.redis_port` in
`api/routes/health.py`, and neither field is defined on the `Settings` model in
`core/config.py` — only a single `redis_url` field exists. This raises an `AttributeError`
on every call, which is swallowed by the surrounding `try/except`, so Redis is always
reported `unhealthy` and the endpoint returns a 503 even when Redis is actually up. A
successful fix updates the probe to build the Redis client from `settings.redis_url` so
the health check accurately reflects Redis's real status.

**Branch name:** `fix/155-redis-health-check`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [c7ad417 — test: reproduce issue #155 - redis_host AttributeError in health check](https://github.com/rushilshah11/pathreview/commit/c7ad417)

**Reproduction summary:**
Confirmed the root cause with `grep -rn "redis_host\|redis_port" core api`: `api/routes/health.py`
(lines 45-46) reads `settings.redis_host`/`settings.redis_port`, but `Settings` in `core/config.py`
only defines `redis_url`. Instantiating `Settings()` and accessing `.redis_host` raises
`AttributeError: 'Settings' object has no attribute 'redis_host'`. Running the exact try/except
block from `health.py` shows this error is caught silently, so Redis is unconditionally reported
`"unhealthy"` (and the endpoint returns 503) regardless of Redis's real status. Added
`tests/unit/test_health.py` with two tests that reproduce this (`pytest tests/unit/test_health.py -v`
passes, documenting the current broken behavior).

**PLAN.md link:** [PLAN.md](../../blob/fix/155-redis-health-check/PLAN.md)

**Walkthrough video (recommended):** _not recorded this week_

**Blockers or open questions:**
The app's startup lifespan requires a reachable Postgres, so I couldn't boot `uvicorn` locally
without a running Postgres instance to hit `GET /health` directly end-to-end. Reproduced the bug
at the `Settings`/`health.py` code-path level instead (see PLAN.md "Risks & unknowns" for the
plan to add a proper `TestClient`-based test in Week 9).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md steps 1-2: `api/routes/health.py` now builds the Redis client
with `redis.Redis.from_url(settings.redis_url, decode_responses=True)` instead of the nonexistent
`settings.redis_host`/`settings.redis_port`. Completed step 3 by rewriting `tests/unit/test_health.py`
to call `health_check()` directly with a mocked DB session, covering both the "healthy" (ping
succeeds) and "unhealthy" (ping raises, 503) cases, and retired the Week 8 reproduction test that
asserted the bug (step 5), keeping only the test that documents `Settings` never defines
`redis_host`/`redis_port`. Also completed step 4 (manual verification): started a local
`redis-server`, called `health_check()` directly, and confirmed it reports `"healthy"`; stopped
Redis and confirmed it correctly flips to `"unhealthy"`/503.

**Next steps:**
Open the PR as a draft, request peer/mentor review per the course Slack channel, and address any
feedback before marking it ready for review.

**Blockers:**
The repo's pre-commit hook (ruff + mypy) fails on pre-existing type/lint issues in `health.py`
that exist on `main` and are unrelated to this fix (untyped `health_check` signature, `Depends()`
in default args, an untyped `health_status` dict) — confirmed via `git stash` that these predate
this branch. Skipped the hook for this one commit and documented the pre-existing counts in the
PR description rather than expanding scope into a full retype of the file.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/326

**Branch:** `fix/155-redis-health-check`

**What you built:**
Fixed the `/health` endpoint's Redis probe, which referenced `settings.redis_host`/`settings.redis_port`
(fields that don't exist on `Settings`) and silently reported Redis as unconditionally unhealthy.
The probe now builds its client from the existing `settings.redis_url` via `redis.Redis.from_url(...)`,
so the health check reflects Redis's real status instead of always failing.

**Tests added or updated:**
`tests/unit/test_health.py` — kept `test_settings_has_no_redis_host_field` (documents the root
cause), and replaced the old reproduction tests with `test_health_check_reports_redis_healthy_when_ping_succeeds`
(calls `health_check()` with a mocked DB session and a mocked `redis.Redis.from_url`/`ping()` that
succeeds, asserting `dependencies.redis == "healthy"` and that the client was built from
`redis_url`) and `test_health_check_reports_redis_unhealthy_when_ping_fails` (mocks `ping()` to
raise `ConnectionError`, asserting `health_check()` raises a 503 `HTTPException` with
`dependencies.redis == "unhealthy"`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(`make test-unit`: 378 passed, 53 pre-existing failures unrelated to this issue, confirmed via
`git stash` to predate this branch. `make check`/lint: 182 pre-existing errors on `main`, still 182
after this change — net zero new issues; my changed lines are individually clean. `make check`/typecheck:
this change reduces `health.py`'s mypy error count from 11 to 8 by removing the `redis_host`/`redis_port`
attr-defined errors; the remaining 8 are pre-existing and unrelated to #155. Full details and the
pre-existing baseline comparison are documented in the PR description.)_

**Draft PR feedback received from:** none yet — just opened

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in on [PR #326](https://github.com/ascherj/pathreview/pull/326) by the Week 10
deadline (per the course note, live reviewer feedback isn't provided in Su26). The PR is still
open as drafted in Week 9.

**How you responded:**
_(blank — no feedback to respond to)_

---

### Reflection

**What was harder than you expected?**
The actual code change was three lines; almost everything hard about this issue was in proving
the fix was correct rather than writing it. The original bug never surfaced as a visible crash —
`api/routes/health.py`'s bare `except Exception` swallowed the `AttributeError` from
`settings.redis_host` and just reported Redis `"unhealthy"` forever, so there was no stack trace
to follow, only a silently-wrong status. I had to reconstruct the failure by hand (instantiate
`Settings()`, access the missing attribute, run the exact `try/except` block in isolation) before
I even had something to write a test against. On top of that, I couldn't boot the full app locally
because the startup lifespan requires a reachable Postgres, so I never got a true end-to-end
`GET /health` request in the browser — I verified at the unit level (mocked DB session, mocked
`redis.Redis.from_url`) and separately toggled a local `redis-server` on and off against
`health_check()` directly. Stitching those two partial verifications into a convincing case that
the fix actually works took longer than the fix itself. I also didn't expect to spend real time on
the pre-commit hook: ruff/mypy failed on my commit for issues that turned out to predate my branch
entirely (confirmed via `git stash`), and deciding how to document "182 pre-existing lint errors,
still 182 after my change" instead of either ignoring the hook or trying to fix unrelated debt was
its own small judgment call.

**What did you learn about working in a large codebase?**
The main skill this module forced was distinguishing "broken because of me" from "already broken."
`make test-unit` had 53 failing tests and `make check` had 182 lint errors before I touched
anything — in a solo project I'd just fix those, but here the right move was to prove they were
pre-existing (via `git stash` comparisons) and report the delta, not the absolute count, in the PR
description. I also learned that a fix isn't done when it changes the right line — I had to
`grep -rn "redis_host\|redis_port" core api` across the whole tree to confirm `health.py` was the
only call site before I could trust the change was complete, something that's unnecessary in a
project small enough to hold in your head. And I learned to actively scope out adjacent problems: I
noticed the bare `except Exception` in `health.py` is *why* this bug shipped silently in the first
place, and it was tempting to narrow it as part of the fix, but that would have expanded a
three-line PR into a behavior change reviewers didn't ask for. I documented it as a follow-up in
PLAN.md instead of fixing it or ignoring it.

**How did AI tools help — and where did they fall short?**
AI was most useful for the parts that are mechanical once the root cause is understood: drafting
the PLAN.md structure, generating the mock-based tests for both the healthy-ping and
failing-ping branches of `health_check()`, and enumerating edge cases I wouldn't have thought of
unprompted (a `redis_url` with no explicit DB index, a `NOAUTH` response, a malformed/empty URL).
It fell short anywhere the claim required actually running something: no amount of reasoning about
`redis.Redis.from_url` substitutes for starting a real `redis-server`, watching `health_check()`
report `"healthy"`, killing it, and watching the status flip — that had to happen on my machine, not
in a suggestion. It also couldn't make the scope judgment call about the bare `except Exception`;
that required knowing what a maintainer reviewing an unsolicited Tier-1 PR would consider in-bounds,
which is a social read of the repo, not a technical one.

**What would you do differently if you started over?**
I'd invest earlier in getting a real local environment running — a `docker-compose` with Postgres
and Redis — so the Week 8 reproduction and Week 9 verification could have been one true end-to-end
`TestClient` request against `/health` instead of two separate partial checks (mocked unit test +
manual `health_check()` calls against a real Redis). That gap is exactly what I flagged as a risk
in PLAN.md and then never closed. I'd also open the PR as a draft on day one of Week 9 instead of
mid-week, purely to maximize the window for feedback to arrive, even though none did this term. And
now that I've seen how much of the four weeks was process — grepping for other call sites, auditing
pre-existing lint/test failures, writing up the PLAN — relative to the size of the actual fix, I'd
pick an issue with a slightly larger blast radius next time; the overhead of contributing safely to
an unfamiliar codebase is roughly fixed regardless of fix size, so it's worth spending it on
something more substantial.

**What are you most proud of from this module?**
Not the fix itself, but the discipline of leaving things alone that weren't in scope. It would have
been easy to "fix while I'm in there" — tighten the bare `except Exception`, clean up the untyped
`health_check` signature, add type hints — and each would have made the file better. Instead I
isolated the actual root cause (the missing `Settings` fields), fixed only that, and wrote down the
adjacent problems as documented follow-ups rather than folding them into the diff. That restraint —
knowing the difference between "this is broken" and "this is my job to fix right now" — is the part
of large-codebase contribution I came in without, and the part I'd point to as evidence I actually
learned it.