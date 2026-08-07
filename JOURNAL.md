## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`health.py` passes a simple query to the database to check it is working. The query must be sent through a specific method, but the execute call receives it as a plain string, which raises an error. As a result, the health endpoint cannot tell whether the database is actually working. Wrapping the query in the required method would let the endpoint report the real database status.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" reasoning:**
This is my first open source contribution. So, I have chosen Tier 1. The issue 154 publisher has already described the cause of the problem and the affected file explicitly. I fully understood what is wrong with the endpoint. This fix is isolated to a single file, so the scope is small enough for me to handle.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rarepig/pathreview/tree/bf543f02befa8a2ab5295f35a600eed55b58b62c

**Reproduction summary:**
Reproduced manually. With the Docker Postgres container confirmed running and
healthy (`docker ps` → `Up (healthy)` on port 5433), calling `GET /health`
returned `"postgres": "unhealthy"`. Since the database is reachable, this is a
false negative caused by the raw `"SELECT 1"` probe in `api/routes/health.py`
(line 31), which raises `ArgumentError` under SQLAlchemy 2.x and is swallowed by
the surrounding `except`.

**Why no existing test catches this:**
There is no test covering `api/routes/health.py`. The project's unit tests mock
the DB session with `AsyncMock` (see `tests/unit/test_review_service.py`), so a
mocked `execute()` never raises the real SQLAlchemy `ArgumentError` — the bug is
invisible to that pattern. Reproducing it requires a live session, as the issue
author notes, which is why I reproduced it manually via `GET /health` + `docker ps`.

**PLAN.md link:** https://github.com/rarepig/pathreview/blob/fix/154-health-db-probe-text/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #154: wrapped the health check's PostgreSQL
probe in `sqlalchemy.text()` (`api/routes/health.py`) and added the required
import. Added a regression test in `tests/unit/test_health.py` that asserts the
probe is called with a `text()` clause. Verified locally: `GET /health` now
reports `postgres: "healthy"`, and the new test passes.

**Next steps:**
Run `make check` and `make test-unit` to confirm no new failures, commit the
fix and test, then open a draft PR against `ascherj/pathreview`.

**Blockers:**
None. (Note: the repo has pre-existing ruff/mypy failures and 53 pre-existing
test failures unrelated to this issue — my change introduces none.)


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/533

**Branch:** `fix/154-health-db-probe-text`

**What you built:**
The `/health` DB probe ran the raw string `"SELECT 1"`, which raises
`ArgumentError` under SQLAlchemy 2.x and made the endpoint falsely report
PostgreSQL as unhealthy even when the database was reachable. Wrapping the query
in `sqlalchemy.text()` fixes this so the probe runs and reports the true
database status. The change is scoped to the Postgres probe only.

**Tests added or updated:**
`tests/unit/test_health.py` — a regression test that calls `health_check` with a
mocked session and asserts the DB probe is invoked with a SQLAlchemy `text()`
clause rather than a raw string. Fails before the fix, passes after.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
Writing the test was harder than I expected. I had to think about edge cases and
other conditions that could raise different kinds of errors. I also had to
isolate my issue from unrelated ones — for example, the redis check (a separate
issue) kept failing, so my test had to focus only on the Postgres probe and
ignore the rest.

**What did you learn about working in a large codebase?**
In my own project, everything is mine, so I understand every part. Here I only
touched a tiny piece (one health-check file) of a much larger multi-service app,
and I learned I don't need to understand the whole thing to fix one bug — I just
need to trace the specific path that matters. I also learned to deal with
pre-existing problems: the repo already had 53 failing tests and many lint
errors that had nothing to do with my issue. So a big part of the work was
separating "what was already broken" from "what I changed," and keeping my change
small and in scope instead of trying to fix everything.

**How did AI tools help — and where did they fall short?**
AI helped me write the test code quickly and understand unfamiliar parts of the
codebase. But even when the generated code runs, it doesn't mean it tests the
right thing — I still had to check that the test actually verifies my fix (that
the probe is called with `text()`), not just that it passes. AI is fast, but
judging whether it's correct is still my job.

**What would you do differently if you started over?**
I would choose a more challenging issue. I picked the one that looked easiest
because I wasn't familiar with writing and reviewing pull requests yet. Now that
I've been through the full workflow once, I feel ready to take on something with
more scope next time.

**What are you most proud of from this module?**
I'm proud that I went through a real contribution workflow end to end — finding
an issue, reproducing it, planning, fixing, testing, and submitting a proper PR
with a clear description. It felt like actual professional work, not just a
classroom exercise.