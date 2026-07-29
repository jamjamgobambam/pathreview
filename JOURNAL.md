# Contribution Journal

## Week 7 — Issue selection

**Issue:** [#155 — Health check references `settings.redis_host`, which does not exist](https://github.com/ascherj/pathreview/issues/155) (Tier 1, `bug`, `api`, `good first issue`)

**Problem summary:**
PathReview's `/health` endpoint is permanently broken: it reports HTTP 503 regardless of actual
system state. The Redis probe reads `settings.redis_host` and `settings.redis_port`, which are
not defined on the `Settings` model — the config exposes Redis as a single `redis_url`. The
resulting `AttributeError` is swallowed by a broad exception handler, so Redis is always marked
unhealthy and the endpoint always escalates to 503. The fix is to construct the client from the
field that exists, via `redis.Redis.from_url(settings.redis_url)`, and to add unit-test coverage
for the endpoint, which currently has none.

**Setup:** Forked [ascherj/pathreview](https://github.com/ascherj/pathreview) to
[salman-khan03/pathreview](https://github.com/salman-khan03/pathreview). Set up a local Python
virtual environment and installed dev dependencies (`pip install -e ".[dev]"`) to run the unit
suite and linters without Docker.

**Branch:** [`fix/155-health-check-redis-config`](https://github.com/salman-khan03/pathreview/tree/fix/155-health-check-redis-config)

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [`685f1ad` — test(api): add regression test reproducing #155 health check crash](https://github.com/salman-khan03/pathreview/commit/685f1ad)

**Reproduction summary:**
Wrote `tests/unit/test_health.py` against the unmodified endpoint and ran it before making any
fix. 3 of 5 tests failed, and the endpoint's own log captured the exact bug:
`redis_health_check_failed  error="'Settings' object has no attribute 'redis_host'"`. This
confirmed the Redis probe never reaches `ping()` and the endpoint always returns 503.

**PLAN.md link:** [PLAN.md](https://github.com/salman-khan03/pathreview/blob/fix/155-health-check-redis-config/PLAN.md)

**Walkthrough video (recommended):** _Not yet recorded._

**Blockers or open questions:**
- The upstream repo's committed `scripts/issues_manifest.json` (130 seed issues) does not match
  the live issue tracker on `ascherj/pathreview` — the manifest's issues are already fixed on
  `main`. Worked from the real, numbered tracker instead (issue #155) once I confirmed this.
- Have not run `make test-integration` (requires Docker services), so the fix is verified at the
  unit level (mocked Redis client) but not against a live Redis instance.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from `PLAN.md`'s Plan section are implemented:
1. Reproduction test written and committed against the unmodified endpoint —
   [`685f1ad`](https://github.com/salman-khan03/pathreview/commit/685f1ad), 3 of 5 tests fail.
2. Minimal fix applied — [`ebcbe72`](https://github.com/salman-khan03/pathreview/commit/ebcbe72):
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)` replaces the two
   nonexistent `settings.redis_host` / `settings.redis_port` fields.
3. `tests/unit/test_health.py` re-run against the fix — all 5 tests pass.
4. Full unit suite compared against a pre-fix baseline: 375 passed / 53 failed before, 380
   passed / 53 failed after (the 5 new tests). The same 53 failures appear in both runs and
   belong to other open issues (#149, #150, #157, #158, and others), not this one.
5. `ruff`, `black`, and `mypy` run on the touched files: `black` clean, `ruff` shows the same 4
   pre-existing errors in `health.py` before and after (none introduced by this change), `mypy`
   error count on `health.py` dropped from 11 to 8 (the removed host/port lines were themselves
   type errors).

`PLAN.md` was rewritten to the required Understand/Map/Plan/Inputs & outputs/Risks &
unknowns/Edge cases structure, and Week 7–8 `JOURNAL.md` entries are complete.

**Next steps:**
Open the PR against `ascherj/pathreview:main` as a draft, request review in the course Slack
channel, address feedback, then mark ready for review and fill in Check-in 2 with the submitted
PR link.

**Blockers:**
No `gh` CLI or GitHub API credentials are available in my local dev environment, so opening the
PR and commenting to claim the issue are manual steps I still need to do through the browser.

---

### Check-in 2 (end of week)

**PR link:** [ascherj/pathreview#383](https://github.com/ascherj/pathreview/pull/383)

**Branch:** `fix/155-health-check-redis-config`

**What you built:**
Fixed the `/health` endpoint, which returned HTTP 503 unconditionally because its Redis probe
read `settings.redis_host` / `settings.redis_port`, fields that don't exist on `Settings`
(Redis is configured as a single `redis_url`). Replaced the broken client construction with
`redis.Redis.from_url(settings.redis_url, decode_responses=True)`, so the probe now reports
Redis's actual reachability instead of always failing.

**Tests added or updated:**
Added `tests/unit/test_health.py` (new file, 5 tests): a config-contract test asserting
`Settings` exposes `redis_url` and not `redis_host`/`redis_port`, a healthy-path test, a test
that the probe is built from the configured URL, a genuine-outage test (mocked
`ConnectionError` still returns 503), and an all-dependencies-healthy test. The reproduction
test was committed separately from the fix (`685f1ad` fails against the bug, `ebcbe72` fixes it)
so the before/after state is visible in history.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(both scoped to the files this PR touches — the codebase has pre-existing lint errors and test
failures unrelated to this issue, documented in the PR description and PLAN.md)_

**Draft PR feedback received from:** none yet

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — not a feature this term (Su26)

**Summary of feedback:**
No reviewer feedback mechanism was available this term. The PR was self-reviewed against
`docs/CONTRIBUTING.md` and the pre-submission checklist instead.

**How you responded:**
N/A — see self-review notes in Check-in 2 above.

---

### Reflection

**What was harder than you expected?**
Trusting the curated issue tracker less than I expected to. My first pick, C-01 (a `KeyError`
on a missing GitHub repo description), turned out to already be fixed on `main` — the code
already guarded with `.get("description") or ""`. The committed
`scripts/issues_manifest.json` (130 seed issues) didn't match the actual live tracker on
`ascherj/pathreview` at all; several of its "bugs," including my first pick, simply weren't
present in the code. I had to check the real GitHub issues (numbered #149–#163+) and verify
each candidate against the actual source before committing to one. I expected the harder part
of this module to be the fix itself; the harder part was actually confirming the problem was
real in the first place.

**What did you learn about working in a large codebase?**
That "does this reproduce" is a real, separate question from "does the issue description sound
plausible" — and skipping straight from the description to a fix is how you end up submitting
a no-op PR. I also learned that a codebase can ship with dozens of known-failing tests on
purpose (this repo had 53 pre-existing unit test failures on a clean checkout, corresponding to
other open issues) and that the job isn't to fix all of them — it's to prove your change doesn't
add to the count. That reframes what "passing tests" even means in a shared codebase: it's a
comparison against a baseline, not an absolute state.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the investigative work: triaging which of 130 candidate
issues were still real by reading the actual source, tracing the bug from the route handler
back to the config schema, and matching the existing test file conventions when writing new
tests. It also helped structure the commit history deliberately — a failing reproduction commit
followed by a one-line fix commit — rather than bundling everything together.

It fell short anywhere that required a real GitHub session or my own judgment: it couldn't post
issue comments, open the PR, or push without my credentials, so all of that stayed manual. It
also couldn't substitute for actually being at the keyboard — partway through the branch got
switched by my own editor while a git operation was in progress, and that needed a human
(me) to notice and confirm nothing was overwritten before continuing.

**What would you do differently if you started over?**
I'd verify the issue against the live code in the first five minutes, before reading the
description closely enough to get attached to it. I picked C-01 partly because it looked like
the cleanest possible first issue, and only discovered it was already fixed after digging in.
A five-minute grep at the start would have saved that detour.

**What are you most proud of from this module?**
Catching the mismatch between the seeded issue manifest and the real tracker before writing any
code against a bug that didn't exist. It would have been easy to open a PR for C-01 that changed
nothing meaningful, and it's the kind of mistake that's invisible until a reviewer points it out.
