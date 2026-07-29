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
