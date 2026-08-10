## Week 7 — Issue selection

**Issue link:** [link](https://github.com/ascherj/pathreview/issues/68)

**Issue title:** Add a safety event count to the health check endpoint

**Tier:** [Y] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]



The /health API endpoint returns health status attributes such as status, dependencies and timestamps (`api/routes/health.py`). However, it does not account for safety events that happened in the last hour. This issue aims to add a safety_events_last_hour value to /health API endpoint result that grabs information from `safety/monitoring.py` so that operators can use /health alone to track the system's health status instead of querying the monitoring dashboard on their own too.

**Branch name:** feat/68-Add-a-safety-event-count-to-the-health-check-endpoint

**Setup confirmation:** [Y] App runs locally at localhost:5173

**Cohort ledger:** [Y] Issue added to cohort ledger

**Is This Issue Right for Me? checklist:**

I can explain what this issue is asking for in my own words, 
I can explain the problem and the expected behavior in 2–3 sentences without reading the issue, and I've located the relevant files and confirmed they exist in the codebase.
Do I understand what "done" looks like?

I can describe what the app should do (or not do) once the issue is fixed, and I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

This issue is a tier 1 issue, and it is my first open source contribution, so it is a realistic match for where I am right now. 

I've found and read the specific code the issue references, 
and I understand the surrounding code well enough to change it safely. I've found the test file for my module and read at least one test end-to-end.
When I signed up, no one was working on this issue. I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue. I also think 
the scope is realistic for Weeks 8–9?

I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline. This issue has no open blockers or dependencies on other unresolved issues.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[link to commit documenting the reproduced issue\]](https://github.com/jesswsong/pathreview/commit/656d3676f46ed98ba541e9be415a214ab073073f)

**Reproduction summary:**
I added a failing test (`tests/unit/test_health_safety_events.py`) that records 8
safety events through `SafetyMonitor` and then calls the `/health` handler. The
test confirms `SafetyMonitor.get_event_count` reports the 8 events, but the health
response's `safety_events_last_hour` comes back as `0` (`assert 0 == 8`). This
pinpoints the gap: `api/routes/health.py` (the block at lines 78–83) hardcodes
`safety_events_last_hour = 0` and never imports or calls `SafetyMonitor`, so the
count in `safety/monitoring.py` is never surfaced. The test is marked
`xfail(strict=True)` so it documents the bug now and will flip to a passing
signal once the fix wires the two files together.

**PLAN.md link:** [PLAN.md](https://github.com/jesswsong/pathreview/blob/feat/68-Add-a-safety-event-count-to-the-health-check-endpoint/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All PLAN.md sub-tasks are implemented:
- Added `core/redis.py` with a `get_redis()` FastAPI dependency (shared client from
  `settings.redis_url`), following the `Depends()` provider convention used by `get_db`.
- Added `SafetyMonitor.get_total_event_count()` in `safety/monitoring.py`, which sums
  `get_event_count()` across all `VALID_EVENT_TYPES`.
- Wired it into `api/routes/health.py`: `safety_events_last_hour` is now populated from
  `SafetyMonitor` instead of the hardcoded `0`. This also fixed the Redis health check,
  which was building a client from the nonexistent `settings.redis_host`/`redis_port`.
- Updated `tests/unit/test_health_safety_events.py`: removed the `xfail` reproduction
  marker and replaced it with two passing tests (total count = 8, and 0 when no events).

I recorded the pre-existing `make check` / `make test-unit` failures before starting and
confirmed my changes introduce none (details in the PR description below).

**Next steps:**
Open a draft PR, request peer/mentor feedback in Slack, and address any feedback before
marking it ready for review.

**Blockers:**
Open question for the maintainer: whether fixing the broken `settings.redis_host`
construction belongs in this PR or a separate issue (I fixed it here since the safety
count needs a working Redis client).

---

### Check-in 2 (end of week)

**PR link:** [\[link to your submitted pull request\]](https://github.com/ascherj/pathreview/pull/735)

**Branch:** `feat/68-Add-a-safety-event-count-to-the-health-check-endpoint`

**What you built:**
The `/health` endpoint now reports a real `safety_events_last_hour` count, summed from
`SafetyMonitor` across all safety event types, instead of a hardcoded `0`. The Redis
client is provided via a new `get_redis()` dependency, which also fixed the endpoint's
previously-broken Redis health check.

**Tests added or updated:**
`tests/unit/test_health_safety_events.py` — two unit tests covering the health endpoint's
safety count: one asserting the total of recorded events, one asserting `0` when none exist.
(`tests/unit/test_monitoring.py` was added in Week 10, after review of the checked-in tests
surfaced a gap — see Week 10 below.)

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Repo has documented pre-existing failures unrelated to this issue — see the PR description's baseline table. My changed files pass ruff/black/mypy individually, and `make test-unit` introduces no new failures vs. the recorded baseline.)

**Draft PR feedback received from:** none — I opened the draft PR and requested
review in the course Slack channel, but no peer or mentor responded before the
deadline.


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
A mentor reviewed my PR and left one comment: "Week 9 updates in JOURNAL.md
missing, but otherwise looks good! The tests are great as well!" So the code
and tests were approved without changes requested, but my Week 9 Check-in 2
entry was still sitting on template placeholders (`[link to your submitted
pull request]`, unchecked self-review boxes) instead of the actual PR link and
a real self-review.

**How you responded:**
I went back and filled in the PR link, branch name, and self-review checkboxes
in Week 9 Check-in 2, and added a note clarifying what "passes" means in a
codebase with a documented pre-existing-failure baseline (my changed files pass
ruff/black/mypy individually; `make test-unit` introduces no new failures
against the recorded baseline, even though the repo-wide run isn't clean). I
also used the review as a prompt to look more critically at my own test
coverage rather than just the journal gap — I added `tests/unit/test_monitoring.py`
with five tests that mock the Redis client directly and cover summing across
all event types, zero events, partial event-type coverage, and a Redis failure
degrading to `0` instead of crashing, since my original test only proved the
`/health` endpoint returned the right number end-to-end without isolating the
summing logic itself.

---

### Reflection

**What was harder than you expected?**
Figuring out where everything actually lived, and how the pieces connected,
before I could touch anything safely. The issue looked like a one-line fix
("populate `safety_events_last_hour` instead of hardcoding `0`"), but that field
needed `SafetyMonitor`, which needed a Redis client, which `health.py` was
already trying to build — except from `settings.redis_host` and
`settings.redis_port`, attributes that don't exist in `Settings` (only
`redis_url` does). So a "safety count" issue turned into tracing a chain: the
placeholder field → the monitor class that could fill it → a broken client
construction blocking it → the actual convention other files used to get a
client at all (`get_db` in `core/database.py`, `get_current_user` in
`api/middleware/auth.py`). Each piece I needed to fix was gated behind
understanding a different piece, and there wasn't a way to shortcut that by
reading just the file the issue pointed at.

**What did you learn about working in a large codebase?**
That a fix isn't really "done" when it produces the right output — it's done
when it fits the codebase's existing shape. I could have hardcoded a Redis
client inline in `health.py` the same broken way the original code did, and it
would have looked like a fix. Reading how `get_db` and `get_current_user` were
already wired as FastAPI dependencies told me that wasn't the right shape, and
that the next person to add a dependency should be able to follow the same
pattern I did. I also learned that "does it pass" is not a single yes/no in a
codebase this size — this repo has hundreds of pre-existing lint/type/test
failures, so I had to record a before/after baseline and prove I hadn't added
to it, rather than just running a check and reading pass/fail off the top line.

**How did AI tools help — and where did they fall short?**
AI was most useful for moving fast through the "where does this connect"
problem — grepping for how other route files obtained a Redis or DB client,
diffing full-repo lint/type/test output before and after my change to get exact
numbers instead of a vague impression, and, when I peer-reviewed a classmate's
PR (#391, a phone-regex fix), checking out their branch in an isolated git
worktree and running their new tests against `main`'s source to confirm the
tests genuinely failed on `main` and passed on their branch, instead of trusting
the PR description's claims at face value. Where it fell short: it didn't
automatically know that the pre-commit hook's mypy scope was broader than
`make typecheck`'s scope (the Makefile target only checks `api/ core/ ingestion/
rag/ agent/ safety/`, not `tests/`) — I ran the narrower command, saw it pass,
and committed anyway, and the hook failed on the same file twice for reasons the
Makefile target couldn't see. That took noticing the discrepancy and verifying
against the actual hook, not just re-running the same wrong command more
carefully.

**What would you do differently if you started over?**
I'd map the dependency chain (field → class → client → convention) before
writing any code, instead of discovering each link only when the previous fix
exposed it — a lot of the "harder than expected" time was serial discovery that
could have been front-loaded into planning. I'd also write the unit tests for
any new method in the same commit as the method itself, instead of leaning on
an end-to-end reproduction test as if it covered the same ground — it took a
reviewer pointing at the journal gap for me to notice the test gap too.

**What are you most proud of from this module?**
Actually taking the time to read through the codebase and understand how the
pieces connect, instead of writing the smallest diff that would make the issue's
example pass. Tracing `health.py` → `SafetyMonitor` → a Redis client → the
`Depends()` convention used elsewhere meant the fix ended up removing a second,
pre-existing bug (the broken `settings.redis_host` construction) as a side
effect of doing it properly, and it's the reason I trusted my own peer review
of someone else's PR enough to actually run their code against adversarial
inputs rather than just reading the diff and approving.

