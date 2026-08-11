# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/129

**Issue title:** Add a database migration validation step to CI that checks all migrations can be applied cleanly

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Scope reasoning ("Is this right for me?"):**
This is a Tier 3 issue with an estimated effort of 5–7 hours, and it's my first
time contributing to this codebase — the checklist points toward Tier 1 for
that situation. I'm choosing to take it on anyway because the scope is well
contained (one new script plus one CI job) and the required skills — shell
scripting, Alembic, and GitHub Actions YAML — are ones I want to build. I'm
flagging the mismatch explicitly rather than pretending it's a Tier 1-sized
task.

**Problem summary:**
Database schema migrations, managed with Alembic under `alembic/versions/`,
are currently only verified manually by whoever is testing a PR — the CI
pipeline in `.github/workflows/ci.yml` runs lint, typecheck, and unit/
integration tests, but never actually applies the migrations to a fresh
database. That means a broken migration (bad SQL, wrong ordering, a missing
downgrade path) can merge to `main` undetected and only surface later in a
real environment. A successful fix adds a CI step — likely a new
`scripts/validate_migrations.sh` invoked from a job in `ci.yml` — that spins
up a throwaway Postgres instance, runs `alembic upgrade head` against it, and
confirms the resulting schema matches what the SQLAlchemy models expect,
failing the build if migrations don't apply cleanly.

**Branch name:** feat/129-migration-validation-ci

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/cbarnes0/pathreview/commit/1a5fb98a9abbc885e58008639e85fbb59936479f

**Reproduction summary:**
Brought up the dev Postgres container and confirmed `alembic upgrade head`
applies both existing migrations cleanly against a fresh database — but
running `pytest tests/integration -v --tb=short`, the exact command the
`test-integration` CI job runs, collects 0 tests and exits 5, since
`tests/integration/` has no test files and nothing else ever invokes
Alembic. I also ran `alembic check` against the freshly migrated database
and it reported real drift already on `main`: migration `001`'s
`uq_users_email` constraint isn't represented in `core/models/user.py`'s
metadata, so "schema matches models" is currently false — this issue is a
real, present gap, not a hypothetical one.

**PLAN.md link:** https://github.com/cbarnes0/pathreview/blob/feat/129-migration-validation-ci/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
The pre-existing `uq_users_email` schema drift needs to be fixed as part of
this PR (see PLAN.md Risks & unknowns) or the new CI check will fail
immediately on `main` after merge — still deciding whether that fix belongs
in this PR or a split-out follow-up issue.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 sub-tasks from PLAN.md are implemented and committed on this branch:
`scripts/validate_migrations.sh` (applies migrations to a fresh DB, then
runs `alembic check` for model drift), a `make migrate-check` target,
a new "Validate migrations" step wired into the `test-integration` CI job,
the `uq_users_email` drift fix in `core/models/user.py` (resolved the open
question from Week 8 — fixed in this PR, not split out, since the new CI
check would otherwise fail immediately on `main`), and a CONTRIBUTING.md
doc update. Along the way I found and fixed a second real bug: the
`test-integration` job's `DATABASE_URL` used a plain `postgresql://` URL,
which `create_async_engine()` in `core/database.py` rejects outright —
latent until now because nothing in that job previously imported
`core.database` or ran Alembic. Added `tests/unit/test_user_model.py` as a
regression test for the constraint fix. Ran `make check` and
`make test-unit` before and after my changes: pre-existing baseline is 182
ruff errors, 52 files needing `black` reformatting, 1 mypy error (a numpy
stub/Python-3.12-syntax incompatibility, unrelated to this change), and 53
failing unit tests — all unchanged after my changes, plus my 3 new tests
passing.

**Next steps:**
Open a draft PR, fill out the PR template (including the pre-existing failures
note above), and ask for peer/mentor review in Slack before marking it ready
for review.

**Blockers:**
None on the implementation. I don't have GitHub CLI auth in my current
working environment, so opening the PR itself is a manual step I'll do
outside this session.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/885

**Branch:** `feat/129-migration-validation-ci`

**What you built:**
A CI step (`scripts/validate_migrations.sh`, wired into the `test-integration`
job) that applies every Alembic migration to a fresh Postgres database and
runs `alembic check` to confirm the resulting schema matches the SQLAlchemy
models, so a broken or drifted migration fails the build instead of merging
silently. Also fixed the real `uq_users_email` drift and a latent
`DATABASE_URL` bug the new check surfaced.

**Tests added or updated:**
`tests/unit/test_user_model.py` — regression coverage for the
`uq_users_email` constraint fix on the `User` model.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(pre-existing failures unrelated to this change are documented in the PR
description and Check-in 1 above — my changes introduce no new failures)

**Draft PR feedback received from:** none — no peer review channel available
this cohort (Su26); PR opened directly as ready for review.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. Per Su26 cohort policy, reviewer feedback isn't provided
this term, so this stayed at "none" through submission.

**How you responded:**
N/A — nothing to respond to.

---

### Reflection

**What was harder than you expected?**
Honestly, nothing. Going in, I expected friction from things like Git Bash
on Windows, the branch/commit conventions, standing up Docker + a Python
venv, or making sense of Alembic's `alembic check` output — but none of it
actually slowed me down. Working with AI to handle the mechanical parts
meant the process stayed smooth the whole way through.

**What did you learn about working in a large codebase?**
Not a lot, honestly. I work in large, unfamiliar codebases at my job
regularly, so navigating PathReview's structure wasn't new territory. What
was genuinely new to me was the specific domain — Alembic migrations and
`alembic check` schema-drift detection, and structuring a validation step
inside GitHub Actions — so there was still something worth learning here,
just not the "large codebase" skill itself.

**How did AI tools help — and where did they fall short?**
AI got the tedious work out of the way — environment setup, drafting the
validation script and CI changes, writing JOURNAL/PLAN scaffolding, and it
even caught the `uq_users_email` schema drift before I would have noticed
it myself. I wouldn't call it "falling short," but there were a handful of
open-ended calls it deliberately left to me — like whether to fix that drift
in the same PR or split it out. That's less a limitation and more just how
working with AI on something like this actually goes: it clears everything
up to the point of a real decision and hands that back.

**What would you do differently if you started over?**
Mostly my attitude. I went in annoyed that this module was a
PR-contribution exercise instead of the MCP or RAG projects I actually
wanted to be building, and that colored the first couple of weeks. If I
started over I'd try to meet the exercise on its own terms instead of
measuring it against the project I wished I were doing instead.

**What are you most proud of from this module?**
Finishing the course. I've enjoyed CodePath overall, and getting this
module closed out is part of that.
