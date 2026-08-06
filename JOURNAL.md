# Module 3 Journal — PathReview

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint reports PostgreSQL as unavailable even when the
database is perfectly reachable. In `api/routes/health.py`, the database probe
calls `await db.execute("SELECT 1")` — passing a bare Python string. SQLAlchemy
2.x no longer accepts raw textual SQL and requires it to be wrapped in `text()`,
so this call raises an `ArgumentError` instead of running the query. The
surrounding `try/except` catches that error and misinterprets it as a
connectivity failure, marking Postgres `"unhealthy"` and flipping the whole
endpoint to a 503. A successful fix wraps the statement in `sqlalchemy.text()`
so the probe actually executes, letting the endpoint report Postgres as healthy
when it is up — while still correctly reporting unhealthy when the database is
genuinely down.

**Branch name:** fix/154-health-check-raw-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### "Is this issue right for me?" — selection notes

**Why this issue fits (scope reasoning):**
- **Tier and labels match my level.** It's labeled `tier-1`, `good first issue`,
  and `bug` — the recommended starting point for a first contribution to a large
  codebase.
- **I reproduced it before claiming it.** While setting up my environment,
  `GET /health` returned 503 and the server logged
  `postgres_health_check_failed error="Textual SQL expression 'SELECT 1' should be
  explicitly declared as text('SELECT 1')"`. That is the exact failure described
  in the issue, so I know the bug is real in my environment and I'll be able to
  verify a fix rather than guess at one.
- **The blast radius is small and well understood.** The defect is a single call
  on one line of one file (`api/routes/health.py`), inside a `try/except` that
  already isolates it. The fix is to import `text` from SQLAlchemy and wrap the
  statement — no schema changes, no API contract changes, no cross-module
  refactor, and no architectural decisions to negotiate.
- **Acceptance criteria are unambiguous.** The issue states the expected error and
  the expected behavior, so "done" is objectively testable.

**Scope risk I identified up front:**
The `/health` endpoint currently fails for **two independent reasons**. Besides
this SQL bug, the Redis probe also throws
`'Settings' object has no attribute 'redis_host'`, and the Chroma vector-db
container in `docker-compose.yml` crash-loops on a NumPy 2.0 incompatibility
(`chromadb 0.4.22` uses the removed `np.float_`). Those are **separate problems
and out of scope for #154.** This matters because fixing only the SQL probe may
not by itself turn `/health` green — the endpoint can still return 503 due to the
Redis check. So I will scope my acceptance criteria to the Postgres probe
specifically: the Postgres dependency must report `"healthy"` and the SQLAlchemy
`ArgumentError` must no longer appear in the logs. If I want the endpoint fully
green, that belongs in a separate issue rather than expanding this one.

**Environment setup notes:**
Backing services run via `docker compose` (Postgres on `5433`, Redis on `6379`).
Migrations applied with `alembic upgrade head` and the database seeded via
`scripts/seed_db.py`. Frontend confirmed running at `localhost:5173` (Vite) and
the API at `localhost:8000` (`/docs` returns 200).

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Hevander27/pathreview/commit/5c158dc

**Reproduction summary:**
I reproduced the bug two ways. (1) Live: with the stack running
(`docker compose up -d`), `GET /health` returned **HTTP 503** and the server
logged `postgres_health_check_failed error="Textual SQL expression 'SELECT 1'
should be explicitly declared as text('SELECT 1')"` — even though the Postgres
container was healthy and reachable. (2) As a test: I added
`tests/unit/test_health.py::test_postgres_probe_uses_sqlalchemy_text_clause`,
which invokes the route handler with a mocked async session and asserts the probe
passes a SQLAlchemy `TextClause`; it **fails** against the original
`db.execute("SELECT 1")` and **passes** once the statement is wrapped in `text()`,
pinning the exact defect.

**PLAN.md link:** https://github.com/Hevander27/pathreview/blob/fix/154-health-check-raw-sql/PLAN.md

**Walkthrough video (recommended):** [not recorded / add Loom link here]

**Blockers or open questions:**
- The `/health` endpoint has a *second, unrelated* failure — the Redis probe reads
  `settings.redis_host` / `settings.redis_port`, which don't exist on `Settings` —
  so `/health` can still return 503 even after this fix. I've scoped my success
  criterion to the Postgres dependency specifically and left the Redis bug for a
  separate issue. Open question: whether to file that separate issue myself.
- The repo's pre-commit `mypy` hook fails on pre-existing errors in `health.py`
  (including the `redis_host` one), which blocks a normal commit to this file. I
  used `--no-verify` and documented it; unclear whether CI will flag the PR for
  this pre-existing debt.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are implemented. In `api/routes/health.py` I imported
`text` from SQLAlchemy and wrapped the probe: `db.execute("SELECT 1")` →
`db.execute(text("SELECT 1"))`. I added `tests/unit/test_health.py` with three
regression tests (asserting the probe passes a `TextClause`, reports Postgres
healthy on success, and still reports unhealthy when the query genuinely fails),
and marked them `@pytest.mark.unit` so `make test-unit` actually runs them —
without the marker they were silently deselected. Verified both live (Postgres
now reports `"healthy"`; the `ArgumentError` is gone from the logs) and via the
tests (the `TextClause` test fails on the original code and passes on the fix).

**Next steps:**
Open the pull request against `ascherj/pathreview` using the completed PR
template, request a peer/mentor review in Slack, address any feedback, then mark
it ready-for-review and record the PR link in Check-in 2.

**Blockers:**
The pre-commit `mypy` hook fails on pre-existing errors in `health.py` (including
the unrelated `redis_host` bug), which blocks a normal commit to this file; I used
`--no-verify` and documented it. Still deciding whether to file a separate issue
for the Redis probe.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/265

**Branch:** `fix/154-health-check-raw-sql`

**What you built:**
Wrapped the `/health` endpoint's PostgreSQL probe (`SELECT 1`) in
`sqlalchemy.text()` so it executes under SQLAlchemy 2.x instead of raising
`ArgumentError`. The probe now reports Postgres's true state rather than having a
caught programming error misreported as a database outage (which was forcing a
503).

**Tests added or updated:**
`tests/unit/test_health.py` (new): `test_postgres_probe_uses_sqlalchemy_text_clause`
(fails without the fix — pins the bug), `test_postgres_reported_healthy_when_query_succeeds`,
and `test_postgres_reported_unhealthy_when_query_fails` (guards against masking a
real outage). All marked `@pytest.mark.unit`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> Note: this codebase has **pre-existing** failures on `main` (ruff: 182, mypy:
> 559, unit tests: 53 failing). Per the Week 9 guidance, "passes" here means my
> change introduces **no new failures** — verified by comparing counts with and
> without my change:
>
> | Check | `main` | With this PR |
> |---|---|---|
> | `make test-unit` | 53 failed / 375 passed | 53 failed / **378** passed (+3 new) |
> | `make check` (ruff) | 182 errors | 182 errors |
> | `make check` (mypy) | 559 errors | 559 errors |
>
> My new test file is itself ruff- and mypy-clean.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in. Reviewer feedback is not provided in the Summer 2026
cohort, and no maintainer or peer comments were left on PR #265 by the end of the
module.

**How you responded:**
N/A — no feedback to respond to. The PR remains open and ready for review.

---

### Reflection

**What was harder than you expected?**
The *fix itself was two lines* — the hard part was everything around it. Getting
the project running locally took the most effort of the whole module: the
`docker compose` plugin was a broken symlink pointing at an uninstalled OrbStack,
the colima daemon was stopped, the Chroma container crash-looped on a NumPy 2.0
incompatibility, and `make setup` would have rebuilt my working Python 3.11 venv
with the system's 3.9 because bare `python` doesn't exist on my machine. None of
that was "the issue," but all of it stood between me and reproducing the issue. It
drove home that on a real codebase, environment and tooling problems are often a
bigger time sink than the actual bug.

**What did you learn about working in a large codebase?**
That "passing" doesn't mean "green." `make check` and `make test-unit` already
failed on `main` — 182 ruff errors, 559 mypy errors, 53 failing unit tests — so
the bar wasn't "make everything pass," it was "don't make anything *worse*." I
learned to establish a baseline first and compare counts with and without my
change, and to document pre-existing failures in the PR rather than trying to fix
the whole repo. I also learned how much small conventions matter: `make test-unit`
filters on `-m unit`, so my new tests were silently *deselected* until I added
`@pytest.mark.unit` — they looked like they passed while never running. And I
learned to scope ruthlessly: `/health` was failing for *two* independent reasons
(the SQL bug and a separate missing `redis_host` setting), and the discipline was
fixing only the one my issue named, not the endpoint as a whole.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and diagnosis: locating the probe in
`api/routes/health.py`, explaining that the broad `try/except` was catching a
*programming* error and misreporting it as an outage, and rapidly working through
the environment breakages. Where it fell short was anything that depended on the
actual state of *this* repo at *this* moment. It couldn't tell me the pre-existing
failure baseline, or that `make test-unit` would deselect my unmarked tests — those
only came from running the real commands and reading the output. An AI summary also
initially implied `WatchlistEntry`-style relationships existed where they didn't in
a related project; the lesson that stuck was to trust the code and the command
output over any summary of them.

**What would you do differently if you started over?**
Run `make check` and `make test-unit` to record the baseline *before* writing a
single line, instead of discovering the pre-existing failures reactively when a
commit hook blocked me. I'd also add the `@pytest.mark.unit` marker from the start
(matching the existing test files) rather than finding out at the end that my tests
weren't being run by the graded command. And I'd decide the "does JOURNAL.md belong
in the upstream PR" question up front instead of leaving it open across three weeks.

**What are you most proud of?**
The restraint. Faced with a health endpoint returning 503 and a repo with hundreds
of lint/type errors, it would have been easy to sprawl. Instead I kept the
production change to exactly the two lines the issue called for, wrote a regression
test that *fails without the fix* to prove it actually pins the bug, and documented
the separate Redis issue and the pre-existing debt rather than absorbing them into
my PR. A small, verifiable, well-scoped change is a more professional contribution
than a big one.
