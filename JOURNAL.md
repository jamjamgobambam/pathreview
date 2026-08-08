# Contribution Journal — PathReview

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's `GET /health` endpoint (in `api/routes/health.py`) checks that
PostgreSQL is reachable by handing the plain string `"SELECT 1"` straight to
SQLAlchemy's `execute()`. SQLAlchemy 2.x no longer accepts a bare string as
executable SQL, so the probe raises `ArgumentError` and the surrounding
`try/except` marks Postgres as `"unhealthy"`, returning HTTP `503` even when
the database is completely healthy — a permanent false outage for any monitor
polling `/health`. A successful fix wraps the query in `sqlalchemy.text()` so
the probe runs under SQLAlchemy 2.x, letting `/health` report `"healthy"` and
`200` whenever the database is actually up, with a unit test guarding against
a raw-string regression. This is a Tier 1 fix scoped to a single file in the
`api` module.

**Issue fit and selection reasoning:**
I chose this as a **Tier 1** issue because it's my first contribution to a
large, multi-service codebase, and the module guidance recommends a
well-scoped Tier 1 issue for newcomers. The scope genuinely fits: the fix is
contained to a single file (`api/routes/health.py`) and effectively one line,
with no schema changes, no database migrations, no cross-module coordination,
and no change to the API contract — so the risk of scope surprises in Week 9
is low. The root cause is a well-documented SQLAlchemy 2.x behavior change,
which means the work is bounded and understandable rather than open-ended. I
estimate 3–6 hours total (fix + unit test + `make check`), which is realistic
for the Week 8–9 window. This lets my first contribution focus on getting the
*process* right (branch naming, conventional commits, tests, PR template)
instead of fighting architectural complexity.

**"Is this right for me?" checklist (all confirmed before claiming):**
- [x] Part 1 — I can explain the issue in my own words; the affected area is
  the `api` module; I can describe a concrete before/after (false `503` while
  DB is up → `200` healthy after the fix).
- [x] Part 2 — Tier 1 is a realistic match for a first contribution; I am not
  reaching for a higher tier to "challenge myself."
- [x] Part 3 — I located and read the exact code (`api/routes/health.py:31`,
  `await db.execute("SELECT 1")`) and its surrounding handler; I noted there
  is no `tests/unit/test_health.py` yet, so I will add one and matched the
  async-mock/pytest pattern used by sibling tests in `tests/unit/`.
- [x] Part 4 — Checked issue comments/ledger claims and am fine with the
  count; scope is realistic for Weeks 8–9; the issue has no open blockers or
  dependencies.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Harsh05dev/pathreview/commit/2347ee4bbfa79cf64f827cdf6009b7fc3f203829

**Reproduction summary:**
I reproduced issue #154 with a unit test (`tests/unit/test_health_repro.py`)
that drives `health_check()` in `api/routes/health.py` with a mock async
session mimicking SQLAlchemy 2.x `execute()` semantics. The raw string
`"SELECT 1"` is rejected with `ArgumentError: Textual SQL expression
'SELECT 1' should be explicitly declared as text('SELECT 1')` (confirmed
against the installed `sqlalchemy 2.0.51`); the broad `try/except` swallows it
and the endpoint falsely reports Postgres `"unhealthy"` and returns HTTP `503`
even though the database is reachable. A second test pins the underlying 2.x
behavior directly (raw string rejected, `text("SELECT 1")` accepted as a
`TextClause`). Both tests pass against the current buggy code, so CI stays
green; they document the reproduction and will be superseded by the fix test
in Week 9.

**PLAN.md link:** https://github.com/Harsh05dev/pathreview/blob/fix/154-health-db-probe-text/PLAN.md

**Walkthrough video (recommended):** _not recorded_

**Blockers or open questions:**
- Nearby latent bug on the same file: `settings.redis_host` is referenced in
  the Redis probe but may not exist on `Settings` (separate issue #155) — out
  of scope for #154, will not touch it.
- Need to confirm the async-mock pattern in the Week 9 `test_health.py` matches
  the sibling tests' style in `tests/unit/` (pytest markers + `pytest-asyncio`
  strict mode, which requires an explicit `@pytest.mark.asyncio`).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Branch:** `fix/154-health-db-probe-text`

**Current progress (sub-tasks completed from PLAN.md):**
- [x] PLAN step 1 — ran `make test-unit` on a clean branch to record a baseline
  *before* any code change: 377 passing, 53 pre-existing failures (in
  `test_review_service.py`, `test_skill_extractor.py`, `test_tech_detector.py`,
  etc.) unrelated to #154.
- [x] PLAN Map / Risk #1 — read `core/database.py` `get_db` and confirmed it
  yields a real SQLAlchemy 2.x `AsyncSession` (built with `async_sessionmaker`,
  `class_=AsyncSession`), so wrapping the probe in `text()` is the correct fix.
- [x] PLAN steps 2–3 — applied the fix in `api/routes/health.py`: added
  `from sqlalchemy import text` and changed the Postgres probe from
  `db.execute("SELECT 1")` to `db.execute(text("SELECT 1"))`.
- [x] PLAN step 4 (started) — drafted `tests/unit/test_health.py`, matching the
  async-mock + `@pytest.mark.asyncio` class-based pattern used by
  `tests/unit/test_review_service.py`.

**Next steps (what remains):**
- Finish and run the two tests; delete the Week 8 repro scaffold
  `tests/unit/test_health_repro.py` (superseded).
- Run `make check` and full `make test-unit`; diff the failing set against the
  baseline to prove zero new failures.
- Fill in the PR template and open the PR against `ascherj/pathreview`.

**Blockers:** None blocking the fix. Note: `make test-integration` cannot run
locally (no Docker services available), so endpoint verification relies on unit
tests plus manual `curl` reasoning.

### Check-in 2 (end of week)

**Branch:** `fix/154-health-db-probe-text`

**Pull request:** https://github.com/ascherj/pathreview/pull/359
(`fix(api): wrap health check DB probe in text()`, `Fixes #154`)

**What I built (summary):** Wrapped the `GET /health` PostgreSQL probe in
`sqlalchemy.text()` so it executes under SQLAlchemy 2.x instead of raising
`ArgumentError` and falsely reporting a reachable database as `"unhealthy"`
(HTTP 503). It is a one-line behavioral change plus one import in
`api/routes/health.py`, covered by new unit tests.

**Tests:**
- **File created:** `tests/unit/test_health.py`. **File removed:**
  `tests/unit/test_health_repro.py` (Week 8 reproduction scaffold, now
  superseded).
- **What they cover:**
  `test_postgres_probe_uses_text_clause_and_reports_healthy` — asserts that with
  a reachable database `dependencies.postgres == "healthy"` **and** that the
  probe is called with a SQLAlchemy `TextClause`; it uses a session double that
  rejects a bare `str` exactly as SQLAlchemy 2.x does, so it doubles as a
  regression guard against re-introducing a raw-string query.
  `test_postgres_probe_reports_unhealthy_on_db_error` — asserts that a genuine
  DB failure is still caught and surfaced as `dependencies.postgres ==
  "unhealthy"` with HTTP 503, so the fix does not swallow real outages.

**Self-review:**
- [x] `make check` passes — my changed files (`api/routes/health.py`,
  `tests/unit/test_health.py`) pass `ruff check` and `black --check`. Repo-wide
  `make check` has failures that exist on `main` before this change (183 `ruff`
  errors + a numpy-stub `mypy` error); I confirmed my change introduces **no new
  lint/type errors**. Documented in the PR's Notes for Reviewers.
- [x] `make test-unit` passes — the two new `test_health.py` tests pass, and the
  full unit suite shows the **same 53 pre-existing failures before and after**
  my change (byte-identical failing set), so I introduced **0 new failures**.
  Documented in the PR's Notes for Reviewers.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review arrived. PR #359 (https://github.com/ascherj/pathreview/pull/359) is
still open against `ascherj/pathreview` with no maintainer comments as of the
Week 10 deadline. Per the Summer 2026 course note, reviewer feedback is not a
feature this term, so I did not expect a maintainer response and none came in.
I re-read my own diff one more time to confirm it still applies cleanly on top
of `main` and that the two `test_health.py` tests still pass.

**How you responded:**
No changes were warranted since there was no feedback to act on. The PR remains
in its submitted state. If a reviewer does respond after the deadline, my plan
is to reply within a day, treat any requested change as a new commit on the
same branch (rather than force-rewriting history), and re-run `make check` and
`make test-unit` before pushing so the reviewer sees a green, reproducible
update.

---

### Reflection

**What was harder than you expected?**
The one-line code change was the easy part; the hard part was *proving* the fix
was safe in a repo that was already failing. When I first ran `make check` and
`make test-unit`, I panicked — 183 `ruff` errors, a `mypy` numpy-stub error,
and 53 failing unit tests. I spent more time establishing that these failures
pre-existed on `main` and were unrelated to `api/routes/health.py` than I spent
on the actual `text()` wrapping. Capturing a byte-identical failing set before
and after my change, so I could claim "0 new failures" with evidence, was the
real work, and it was harder and slower than I anticipated for a Tier 1 issue.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is mostly about respecting
boundaries and proving you didn't break anything, not about writing clever code.
On my own projects I'd just fix a bug and move on; here I had to read
`core/database.py` to confirm `get_db` actually yields a SQLAlchemy 2.x
`AsyncSession` before I could trust that `text()` was even the right fix, and I
had to match the existing async-mock + `@pytest.mark.asyncio` pattern from
`tests/unit/test_review_service.py` instead of inventing my own test style. I
also learned to leave nearby bugs alone — I spotted a likely `settings.redis_host`
problem in the same file but scoped it out as a separate issue (#155) rather
than expanding my PR.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and pattern-matching: quickly explaining the
SQLAlchemy 2.x behavior change (raw string → `ArgumentError: Textual SQL
expression 'SELECT 1' should be explicitly declared as text(...)`), and helping
me shape a session double that rejects a bare `str` exactly the way 2.x does so
my test doubles as a regression guard. Where it fell short was judgment about
*this specific repo's* messy state — no tool could tell me whether the 53
failing tests were my fault or pre-existing; I had to run the baseline myself,
diff the failing sets, and decide what was in scope. It also couldn't run
`make test-integration` for me (no Docker services locally), so I had to reason
about the endpoint behavior manually instead of relying on generated answers.

**What would you do differently if you started over?**
I'd capture the clean-branch test baseline in Week 8 during reproduction, not in
Week 9 during the fix. I recorded the 377-pass / 53-fail baseline late, and
having it earlier would have saved me the mid-week panic and let me plan the
"0 new failures" evidence from the start. I'd also record the optional
walkthrough video — I skipped it, and explaining the before/after out loud would
have forced me to tighten my reasoning about why `text()` is the correct fix
earlier in the process.

**What are you most proud of from this module?**
I'm most proud that my test doubles as a regression guard, not just a green
checkmark. `test_postgres_probe_uses_text_clause_and_reports_healthy` asserts
the probe is called with an actual `TextClause` and uses a session double that
rejects a raw string the way SQLAlchemy 2.x does — so if someone later reverts
`text("SELECT 1")` back to `"SELECT 1"`, the test fails instead of silently
passing. For a first contribution to an unfamiliar production codebase, landing
a fix that actively prevents its own regression feels like getting the process
right, which was my whole goal in picking a Tier 1 issue.
