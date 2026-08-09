# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint checks that PostgreSQL is reachable by running
`await db.execute("SELECT 1")`, passing the query as a plain Python string.
SQLAlchemy 2.x no longer accepts raw string SQL in `execute()` — the statement
must be wrapped in `sqlalchemy.text()` — so this call raises an error and the
Postgres probe is reported as `unhealthy` even when the database is perfectly
fine. Because any unhealthy dependency flips the overall status, the endpoint
then returns HTTP 503, which can falsely trip uptime monitors and deployment
health gates. A successful fix wraps the query in `text()` (and imports it) so
the probe executes correctly and reports the true database status. The change
is isolated to `api/routes/health.py`, backed by a unit test asserting the
endpoint returns 200 when the database is up.

**Branch name:** fix/154-health-check-db-probe

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes — "Is this right for me?" checklist

- **Scope is small and well-bounded.** The defect and its fix live in a single
  file (`api/routes/health.py`, line 31). I confirmed this by reading the file
  directly rather than trusting the title.
- **I understand the root cause.** SQLAlchemy 2.x removed implicit autocommit
  and "plain string" execution; textual SQL must go through `text()`. This is a
  well-documented, canonical migration issue, not an obscure edge case.
- **The fix is verifiable.** I can prove the fix with a focused unit test on the
  health endpoint (expect 200 + `postgres: "healthy"` when the DB is up), which
  fits the project's "every change includes a test" standard.
- **No hidden dependencies.** The fix doesn't touch the LLM/RAG/agent pipeline,
  so it doesn't require an OpenRouter API key or model access to validate.
- **Right difficulty for a first contribution.** Labeled `good first issue` /
  `tier-1`, estimated at 1–2 hours, and it teaches a real, transferable lesson
  about the SQLAlchemy 1.x → 2.x API change.

**Conclusion:** Good fit — clear cause, single-file change, easily tested, and
independent of external services.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Prasanna401623/pathreview/commit/8de9e4b8953a0f84b4fc16ad5cc89ecb7430803b

**Reproduction summary:**
I added a focused unit test (`tests/unit/test_health_check.py`) using an
in-memory SQLite engine on the app's own SQLAlchemy 2.0.51, and confirmed that
`execute("SELECT 1")` raises `ObjectNotExecutableError: Not an executable
object: 'SELECT 1'`, while `execute(text("SELECT 1"))` returns `1`. End-to-end,
hitting `GET /health` locally returned HTTP 503 with `"postgres": "unhealthy"`
even though the Docker database container was healthy — exactly the false
"database down" report described in the issue.

**PLAN.md link:** https://github.com/Prasanna401623/pathreview/blob/fix/154-health-check-db-probe/PLAN.md

**Walkthrough video (recommended):** Not recorded (optional / not graded).

**Blockers or open questions:**
- The same endpoint has a separate bug (#155, `settings.redis_host`), so my
  Week 9 test must assert specifically on the `postgres` dependency rather than
  the overall 200, to avoid coupling to someone else's issue.
- `aiosqlite` isn't installed, so I still need to decide how to drive the async
  probe in a test — a FastAPI dependency override with a stub session, or an
  integration test against the local Postgres.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Sub-tasks 1, 2 and 4 from `PLAN.md` are done. I added
`from sqlalchemy import text` to `api/routes/health.py` and changed the Postgres
probe from `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))`,
leaving the surrounding `try`/`except` intact so real outages are still reported.
I also captured a **baseline** of `make check` and `make test-unit` on the
unmodified file before touching anything, because the repo turned out to have a
lot of pre-existing breakage (182 ruff errors, 53 failing unit tests) that has
nothing to do with #154.

Two things I found that weren't in the plan:
- My Week 8 reproduction tests had **no `@pytest.mark.unit` marker**, so
  `make test-unit` (which runs `-m unit`) was silently deselecting them. They
  showed up as `2 deselected` and had never actually run in the suite.
- Those Week 8 tests only exercised SQLAlchemy in isolation with a SQLite
  engine. They never imported `health.py`, so they'd have passed whether or not
  the bug was fixed. They weren't real regression tests.

**Next steps:**
Sub-task 3 — rewrite `tests/unit/test_health_check.py` to drive `health_check()`
directly. I resolved the open question from Week 8 (how to drive the async probe
without `aiosqlite`): rather than a FastAPI dependency override or a live
Postgres, I'm writing a `StubAsyncSession` that mimics SQLAlchemy 2.x
`execute()` strictness by raising `ObjectNotExecutableError` when handed a bare
string. That keeps the test a true unit test and makes a regression to
`execute("SELECT 1")` fail loudly. Then sub-task 5, and open the PR.

**Blockers:**
None blocking. One annoyance: the project's `pre-commit` hook can't pass on
`api/routes/health.py` at all — `ruff` trips on `B008` (`Depends()` in an
argument default, the standard FastAPI idiom) and `mypy` trips on pre-existing
untyped-dict errors. Both pre-date my change. I'll commit with `--no-verify` and
document it in the PR rather than re-typing a function this issue isn't about.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/869

**Branch:** `fix/154-health-check-db-probe`

**What you built:**
The `/health` PostgreSQL probe passed raw SQL as a plain Python string, which
SQLAlchemy 2.x refuses to execute — so the probe raised on every request, the
broad `except Exception` swallowed the real error and marked the database
`"unhealthy"`, and `GET /health` returned HTTP 503 even when Postgres was
completely fine. The fix wraps the statement in `sqlalchemy.text()`, so the
probe now reports the database's actual state instead of its own bug. The
`try`/`except` is unchanged, so genuine outages still report unhealthy.

**Tests added or updated:**
`tests/unit/test_health_check.py` — rewritten. `TestPostgresHealthProbe` (4
tests) drives `health_check()` itself through a `StubAsyncSession` that rejects
bare strings the way SQLAlchemy 2.x does: a reachable DB reports `"healthy"`,
the probe hands over a `TextClause` rather than a string, a genuine outage still
reports `"unhealthy"`, and that outage still surfaces as HTTP 503.
`TestSqlAlchemyTextRequirement` (2 tests) keeps the root-cause documentation and
justifies the stub's strictness. Both classes are now marked `unit` so the suite
actually selects them.

I verified the tests are real by reverting `health.py` to the buggy version:
2 of the 6 fail without the fix and all 6 pass with it. The tests assert on
`health_status["dependencies"]["postgres"]` rather than an overall HTTP 200,
because the Redis probe in the same endpoint is independently broken by #155 —
which I deliberately did not touch.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both in the "introduces no new failures" sense, which is what this codebase
allows — I documented the baseline in the PR description:

| Command | Before | After |
| --- | --- | --- |
| `make lint` | 182 ruff errors | 182 ruff errors |
| `make typecheck` | 5 errors in 4 files | 5 errors in 4 files |
| `make test-unit` | 53 failed, 375 passed, 2 deselected | 53 failed, 381 passed, 0 deselected |

The 53 failures are byte-for-byte identical before and after (`diff` of the
sorted `FAILED` lines is empty), and none are in files I touched. My changes add
6 passing tests and reduce `api/routes/health.py` from 4 ruff errors to 1.

**Draft PR feedback received from:** none — I opened the PR ready-for-review
rather than as a draft, so I have not yet had a peer look at it. I'll post it in
the cohort Slack channel and fold in any feedback as review commits.

**What I learned:**
The most useful thing this week wasn't the one-line fix — it was discovering my
Week 8 tests were both deselected *and* incapable of failing. "The tests pass"
means nothing until you've watched them fail for the right reason. Reverting the
fix to confirm the tests break is now a step I'll always do.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. PR
[ascherj/pathreview#869](https://github.com/ascherj/pathreview/pull/869) has been
open since Aug 5 and is still `OPEN` with zero review comments and zero submitted
reviews (`reviewDecision: REVIEW_REQUIRED`, no line comments, no maintainer
reply). Per the Summer 2026 course note, reviewer feedback isn't part of this
term, so this is the expected outcome rather than a stalled PR.

**How you responded:**
Nothing to respond to, so I did the next best thing and reviewed the PR against
itself. I re-read my own diff cold, confirmed the branch still applies to
`upstream/main` without conflict, and re-ran the verification I'd claimed in the
PR description — reverting `api/routes/health.py` to `await db.execute("SELECT 1")`
and watching 2 of the 6 tests in `tests/unit/test_health_check.py` fail, then
restoring the fix and watching all 6 pass. I made no new commits to the fix
itself; changing working code with no reviewer asking for it would only make the
diff harder to review when someone does pick it up. The one thing I'd have
pre-empted a reviewer on is already in the PR body: the before/after baseline
table showing the repo's 182 ruff errors and 53 failing unit tests are unchanged
by my branch, and the note that I committed with `--no-verify` because the
project's own pre-commit hook cannot pass on that file.

---

### Reflection

**What was harder than you expected?**
Two things, neither of them the actual bug.

The first was that the repository has no green baseline. I assumed "make check
passes" was a state I could reach; it isn't. On an untouched clone, `make lint`
reports 182 ruff errors, `make typecheck` reports 5, and `make test-unit` reports
53 failures. So "my change is clean" had to be redefined as "my change introduces
no new failures," which meant capturing a baseline *before* editing anything and
diffing the sorted `FAILED` lines before and after. I didn't think to do that
until Week 9, and if I'd edited first I would have had no way to prove which
failures were mine. Worse, the project's own `pre-commit` hook cannot pass on
`api/routes/health.py` — ruff flags `B008` for `Depends()` in an argument
default, which is the standard FastAPI idiom, and mypy flags pre-existing untyped
dicts. Deciding to commit with `--no-verify` and document it, rather than
"fixing" a function my issue wasn't about, was a genuinely uncomfortable call.

The second was discovering my Week 8 reproduction tests were worthless in two
independent ways at once. They had no `@pytest.mark.unit` marker, so `make
test-unit` (which runs `-m unit`) was silently deselecting them — they showed as
`2 deselected` and had never once run in the suite. And even if they had run,
they only exercised SQLAlchemy against a SQLite engine; they never imported
`health.py`, so they would have passed identically whether or not the bug was
fixed. I had written a test that could not fail. Nothing in the output told me
this. I found it only because the deselection count looked wrong.

The smaller surprise: `api/routes/health.py` contains *two* unrelated bugs. Mine
(#154, the Postgres probe) and #155 (`settings.redis_host` doesn't exist on
`Settings`), about ten lines apart. Because #155 independently forces the
endpoint to 503, I couldn't write the obvious test — "assert `GET /health`
returns 200." I had to assert on
`health_status["dependencies"]["postgres"]` specifically, and leave a bug I could
see and could have fixed in about two minutes completely alone.

**What did you learn about working in a large codebase?**
That the code is the easy part. My actual change is two lines: an import and a
`text()` wrapper. Everything else — three weeks of it — was figuring out what
"done" means in someone else's house.

In my own projects I'm both the author and the standard. `CLAUDE.md` in my
personal repo says ESLint and `tsc --noEmit` must be clean before every commit,
and they are, because I wrote that rule and I've never let it rot. In PathReview
the equivalent rule exists on paper and the repo has drifted a long way from it,
and I don't get to decide that's unacceptable — I get to leave it exactly as I
found it and prove I did. Contributing means your diff is judged relative to the
repo's current state, not relative to ideal.

Scope discipline turned out to be a real skill and not just etiquette. Fixing
#155 while I was already in the file would have felt helpful and would have made
my PR strictly worse: it would have mixed two issues, made the diff harder to
review, and stepped on whoever was assigned #155. The instinct to "clean up while
I'm here" is the right instinct in my own repo and the wrong one in someone
else's.

And the project's conventions are load-bearing and invisible. The pytest marker
that decides whether your test runs at all isn't announced anywhere in the test
file; it's a config detail you either notice or don't. I now read the Makefile
and the pytest config before writing a single test, because they define what
"running the tests" actually means.

**How did AI tools help — and where did they fall short?**
Most useful on the parts with a known right answer. The SQLAlchemy 1.x → 2.x
migration — why bare strings stopped executing, what `ObjectNotExecutableError`
means, that `text()` is the canonical fix — I got in a couple of minutes instead
of half an hour of docs. It was also good at mechanical scaffolding: drafting the
`StubAsyncSession` and `StubResult` shape, writing the docstrings, and helping me
turn a wall of pytest output into a clean sorted diff of failures.

Where it fell short is the more interesting half. In Week 8 the suggested testing
paths were an in-memory async SQLite engine or a FastAPI dependency override —
both reasonable in the abstract, and the first was flatly impossible because
`aiosqlite` isn't installed in this project. That's the pattern: confident advice
about a generic FastAPI app, not about *this* one. The stub-session approach I
eventually used, which mimics SQLAlchemy 2.x's strictness by raising
`ObjectNotExecutableError` on a bare string, came from reasoning about what my
test actually needed to be capable of catching, and it's better than either
suggestion because a regression to `execute("SELECT 1")` fails it loudly.

Nothing flagged that my Week 8 tests were deselected, and nothing flagged that
they were incapable of failing — the code looked like a test and read like a
test. Only reverting the fix and watching what happened proved otherwise. Same
with #155: recognizing that the second bug in the file was someone else's and
that it had to change how I wrote my assertion was a judgment about the project
and the cohort, not about the code. AI was a fast reference and a decent
drafting partner; it was not a substitute for running the thing and for knowing
where the boundaries of my change were.

**What would you do differently if you started over?**
Capture the baseline in Week 7, in the same sitting as the setup confirmation.
Running `make check` and `make test-unit` on an untouched clone and saving the
output takes five minutes and would have saved me a genuinely anxious hour in
Week 9 wondering how many of those 53 failures I had caused.

Write the reproduction test against the real function immediately. My Week 8
"reproduction" proved that SQLAlchemy rejects bare strings, which is a fact about
SQLAlchemy, not about PathReview. It should have imported `health_check` from day
one. The rule I'd give my Week 8 self: if reverting the fix wouldn't break your
test, you haven't reproduced anything.

Run the project's own test command, not `pytest`, from the very first test. The
marker problem was invisible under a bare `pytest` invocation and obvious under
`make test-unit`.

And I'd open the PR as a draft. I opened #869 ready-for-review because it *was*
ready, which was technically correct and tactically wrong — a draft is the
posture that actually invites a peer to look, and I gave up my one shot at
feedback in exchange for nothing.

**What are you most proud of from this module?**
Catching that my own tests couldn't fail, and then proving the replacements
could. It would have been very easy not to notice: the suite was green, the fix
was correct, the PR would have looked identical from the outside. I'd have
shipped a real fix guarded by a test that would never catch its regression, and
felt fine about it. Instead I reverted `health.py` to the buggy line, confirmed
that 2 of the 6 tests fail without the fix and all 6 pass with it, and wrote that
verification into the PR description so a reviewer doesn't have to take my word
for it. The two-line fix is the deliverable; knowing the difference between a
test that passes and a test that works is the thing I actually took away.
