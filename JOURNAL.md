# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` tries to connect using
`settings.redis_host` and `settings.redis_port`, but the `Settings` config class only
defines a single `redis_url` field — those two attributes don't exist. As a result, the
Redis check always throws an `AttributeError`, and the whole health endpoint reports
"unhealthy" even when Redis is running fine. A correct fix connects using the existing
`redis_url` (e.g. via `redis.Redis.from_url()`) so the health check accurately reflects
Redis's real status. This also has zero existing test coverage, so part of the fix is
adding a test for the `/health` endpoint.

**Scope reasoning:** This is my first open-source contribution, so I chose a Tier 1 issue
per the checklist. It's isolated to one function in one file, the root cause is already
confirmed by reproducing the bug locally, and it's realistically a 1-2 hour fix plus test
writing — well within the Tier 1 time estimate. This issue already has significant activity
from other students (several claim comments and a few open PRs); per the contribution
checklist, claims are non-exclusive and my grade comes from my own artifacts, so I'm
proceeding, but will implement and write it up independently rather than referencing
anyone else's PR.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/BettinaGeorge/pathreview/commit/a9dcec0

**Reproduction summary:**
I wrote `tests/unit/test_health.py`, which calls `health_check()` directly with a mocked
database dependency. One test confirms the root cause directly — the real `Settings`
object has no `redis_host`/`redis_port` fields, only `redis_url`. The second test calls
the actual route function and confirms it raises `HTTPException(503)` with
`dependencies.redis == "unhealthy"` even though Postgres reports healthy — proving the
`AttributeError` from the missing settings field is silently caught by the route's broad
`except Exception` block rather than surfacing as a crash.

**PLAN.md link:** https://github.com/BettinaGeorge/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Before implementing the fix, I need to grep the codebase for any other `redis.Redis(...)`
call sites to confirm `api/routes/health.py` is the only place that needs to change.
Separately, running mypy against this file surfaced several pre-existing type errors in
`health.py` unrelated to this issue (missing type annotations, dict-indexing errors on a
loosely-typed `health_status` object) — I bypassed the pre-commit hook for my reproduction
commit since those errors predate my change, but I'll decide in Week 9 whether cleaning
them up belongs in this PR's scope, since I'll already be editing that exact function.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed sub-tasks 1-2 from `PLAN.md`: grepped the codebase for other `redis.Redis(...)`
call sites and confirmed `api/routes/health.py` is the only one, then replaced the broken
`redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)` construction with
`redis.Redis.from_url(settings.redis_url, decode_responses=True)`.

**Next steps:**
Update `tests/unit/test_health.py` (sub-task 4) so it verifies the fixed behavior instead
of just documenting the bug — flip the end-to-end test to expect `"healthy"`, and add a
new test confirming a genuinely unreachable Redis is still correctly reported as
`"unhealthy"`. Then run `make check` and `make test-unit` to confirm no new failures
(sub-task 5), and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/990

**Branch:** fix/155-health-check-redis-host

**What you built:**
Fixed the `/health` endpoint's Redis probe, which crashed with an `AttributeError` because
it referenced `settings.redis_host`/`settings.redis_port` — fields that don't exist on
`Settings` (only `redis_url` does). The endpoint now connects via
`redis.Redis.from_url(settings.redis_url)`, so it correctly reports Redis's real status
instead of always returning a 503.

**Tests added or updated:**
Updated `tests/unit/test_health.py` (3 tests total): one confirms the root cause directly
(`Settings` has no `redis_host`/`redis_port` fields, only `redis_url`), one confirms a
reachable Redis now reports `"healthy"` with a 200 response instead of the old 503, and one
covers the edge case that a genuinely unreachable Redis still correctly reports
`"unhealthy"` rather than the fix silently masking real outages.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: this codebase has documented pre-existing failures unrelated to this issue —
53 pre-existing test failures across 16 unrelated files, 100 pre-existing mypy errors
across 26 files including 8 in `health.py` itself, and 183 pre-existing ruff errors in
files I didn't touch. I confirmed all of these counts are identical before and after my
change, so "passes" here means my change introduces no new failures, per the
pre-existing-failures guidance for this week. Full breakdown is documented in the PR
description.)

**Draft PR feedback received from:** none — opened directly as ready for review due to
the submission deadline having passed; reaching out to the course team separately about
the late submission.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — reviewer feedback is not provided this term (Su26)

**Summary of feedback:**
No reviewer feedback came in — per the course note this term, reviewer feedback isn't a
feature in Summer 2026, so my PR (#990) remains open without comments as of this writing.

**How you responded:**
N/A — nothing to respond to. If feedback comes in after this entry, I'll update this
section.

---

### Reflection

**What was harder than you expected?**
Honestly, the hardest part wasn't the code — it was making sure I stayed the one actually
driving this instead of just letting Claude take over. It would generate the fix, write
the tests, draft the PR description, and it was really easy to just say "okay, do that"
without stopping to actually understand what had changed or why. A few times I caught
myself about to run a command without really knowing what it did. I had to be intentional
about slowing down — asking it to explain things, running commands myself instead of
letting it run everything, actually reading the output before moving to the next step —
especially during the environment setup debugging (the Python version mismatch, the
Postgres port conflict), where it would've been easy to just follow instructions blindly
and end up with a working setup I didn't actually understand.

**What did you learn about working in a large codebase?**
The biggest shift was learning that "does my change work" and "does the whole test suite
pass" are different questions in a real codebase. When I ran `make check` and
`make test-unit` on this fork, I found 183 pre-existing lint errors, 100 pre-existing
mypy errors, and 53 pre-existing failing tests — none of which had anything to do with my
issue. I had to learn to isolate what I was responsible for: confirming my specific files
introduced nothing new, documenting the baseline honestly, and not scope-creeping into
fixing unrelated debt just because I happened to be in the neighborhood. I also learned to
actually grep for other call sites of the pattern I was fixing before assuming my change
was complete and isolated.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for fast triage — reading a stack trace or `lsof` output and
immediately narrowing down "this is a port conflict, not a credentials issue," or spotting
that a mypy failure I was staring at was pre-existing and unrelated to my diff. It was also
useful for scaffolding tests that matched the existing repo's patterns (fixtures, markers,
`AsyncMock` usage) instead of inventing my own style. Where it fell short was anything that
depended on the actual state of my machine — it couldn't know my shell wasn't sourcing
pyenv, or that a specific port was already taken, until I ran commands and reported back
real output. It also couldn't make the judgment call on scope for me — deciding whether to
fix the pre-existing mypy debt in `health.py` while I was already in that file was a
tradeoff I had to reason through myself, not something to defer to a tool.

**What would you do differently if you started over?**
I'd set up pyenv and shell integration correctly before ever running `make setup`, instead
of debugging it live once things broke. I'd also run `make check` and `make test-unit` as
an immediate baseline right after setup — before touching any code — rather than
discovering the pre-existing failure counts reactively in the middle of Week 9. And for
issue selection, I'd weigh "how crowded is this issue" more heavily up front; #155 turned
out to have 10+ claim comments and three other open PRs by the time I submitted mine,
which didn't affect my grade but meant less room for original peer discussion around it.

**What are you most proud of from this module?**
Just finishing my first real open source contribution, honestly. Actually getting a PR up
on someone else's repo, following their contribution standards, working through a
codebase I didn't write and didn't fully understand going in — I wasn't sure at the start
that I'd make it all the way to a submitted PR. Now that I've seen what the process
actually looks like end to end, I'm genuinely looking forward to taking on more open
source issues after this.
