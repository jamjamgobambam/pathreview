## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/129

**Issue title:** Add a database migration validation step to CI that checks all migrations can be applied cleanly

**Tier:** [ ] Tier 1 [ ] Tier 2 [x] Tier 3

**Problem summary:**
PathReview has SQLAlchemy models and Alembic migration files, but its CI workflow does not currently verify the database migration history. A migration can therefore be syntactically valid while failing against a clean PostgreSQL database or leaving the database schema inconsistent with the application models. The requested change will create a fresh database in CI, apply every migration in order, and compare the resulting schema with the SQLAlchemy metadata. This will catch migration failures and schema drift before a pull request is merged.

**Selection rationale:**
I can identify the relevant CI, Alembic, and SQLAlchemy files and explain the difference between application models, migration history, and the live database schema. The issue is a stretch because it crosses PostgreSQL, Alembic, shell scripting, and GitHub Actions, but the repository currently has a short two-migration history and a working PostgreSQL service pattern in the existing integration-test job. I chose it to build database and CI skills that complement my Python, SQL, statistics, and machine-learning background. The main scope risk is defining a reliable schema-consistency check and reproducing the same behavior locally and in GitHub Actions.

**Branch name:** feat/129-database-migration-validation

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort Ledger:** [x] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/CocoYang10/pathreview/commit/a25a659

**Reproduction summary:**
I reproduced this as a missing CI safeguard: the repository has an ordered
Alembic history (`001 -> 002`), but `.github/workflows/ci.yml` never runs it. On
a fresh local PostgreSQL 16 database, both migrations applied successfully,
but `alembic check` then detected an extra `uq_users_email` constraint, proving
that the migrated schema already drifts from the SQLAlchemy models while the
current CI has no check that reports it.

**PLAN.md link:** https://github.com/CocoYang10/pathreview/blob/feat/129-database-migration-validation/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The live database reproduction is complete. The remaining implementation
question is how narrowly to correct the confirmed drift: the new revision must
remove only the redundant `uq_users_email` constraint while preserving the
unique `ix_users_email` index that still enforces email uniqueness. The same
successful-failure sequence must then be reproduced in GitHub Actions to prove
the new CI job is using the intended async PostgreSQL connection.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** I traced the drift to migration `001`, which creates both
a unique constraint and a unique index for `users.email`, while the current
SQLAlchemy metadata expects only the unique index. I added a new corrective
migration instead of modifying published migration history, and started a
reusable validation script plus a separate PostgreSQL-backed CI job.

**Next steps:** Add focused tests, recreate a clean PostgreSQL database, run the
full migration chain and schema comparison, then self-review the final diff.

**Blockers:** The repository's existing test and lint suites are not green, so I
need to compare before-and-after results and demonstrate that this change adds
no new failures rather than claiming to fix unrelated baseline problems.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/849

**Branch:** `feat/129-database-migration-validation`

**What you built:** I added migration `003` to remove the redundant
`uq_users_email` constraint without removing the unique index, a fail-fast shell
script that runs `alembic upgrade head` followed by `alembic check`, and a new
GitHub Actions job that executes this workflow against fresh PostgreSQL 16.

**Tests added or updated:** I added four unit tests for the complete revision
chain, the corrective migration's upgrade and downgrade operations, and the
validation script's missing-`DATABASE_URL` behavior. All four pass. I also ran
the real workflow against a recreated local database: migrations `001` through
`003`, rollback and reapplication of `003`, and the final schema comparison all
passed. The full unit-suite baseline remained unchanged at 52 failures and 31
errors, with passing tests increasing from 345 to 349.

**Self-review confirmation:** [ ] `make check` passes [ ] `make test-unit`
passes. Both commands still fail on documented pre-existing repository issues;
focused Ruff, Black, shell syntax, and the four new tests pass, and no new full
suite failures were introduced.

**Draft PR feedback received from:** None yet.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No review feedback has come in on PR #849. I checked the PR again before
completing this reflection and found no reviewer comments, submitted reviews,
or inline review threads.

**How you responded:**
No response or code change was needed because no feedback was received.

---

### Reflection

**What was harder than you expected?**
The hardest part was understanding that there are three related but different
versions of the database structure: the SQLAlchemy models, the Alembic migration
history, and the schema that actually exists in PostgreSQL. At first, I assumed
that if `alembic upgrade head` completed successfully, the migrations were
correct. The surprising part was that revisions `001` and `002` both ran, but
`alembic check` still found schema drift because `users.email` had both a unique
constraint and a unique index. I also had to learn how to judge my change in a
repository whose full test and lint suites already had many failures. Comparing
the baseline before and after my work was more useful than treating every red
result as something caused by my PR.

**What did you learn about working in a large codebase?**
I learned that one issue can cross more modules than its title suggests. This
issue involved GitHub Actions, a shell script, Alembic configuration and revision
files, SQLAlchemy models, PostgreSQL, and tests. I could not make a responsible
change by reading only `.github/workflows/ci.yml`; I had to trace how the
database URL is loaded, how Alembic imports the model metadata, and how the
existing migrations build the schema. I also learned why contributors should
not rewrite an old migration that may already have run in other environments.
Adding revision `003` preserved the shared history and corrected existing
databases through the same ordered process.

**How did AI tools help — and where did they fall short?**
AI tools were most helpful for explaining unfamiliar concepts in smaller steps,
mapping the relevant files, and turning the issue into a testable plan. They
also helped me compare CI, Alembic, SQLAlchemy, and PostgreSQL as parts of one
workflow instead of isolated tools. However, an explanation or suggested patch
was not evidence that the migration really worked. I still needed to inspect
the repository, install and run PostgreSQL, reproduce the drift, and test the
upgrade, check, downgrade, and re-upgrade myself. AI also could not decide that
the repository's existing failures were harmless without a before-and-after
baseline. The useful boundary was to use AI for orientation and reasoning, then
use the actual code and database as the source of truth.

**What would you do differently if you started over?**
I would run and record the repository's complete test and lint baseline at the
very beginning. I eventually did this, but doing it before implementation would
have made the scope clearer and reduced confusion when the full checks failed.
I would also draw the relationship between models, migrations, and the live
schema before changing code. That mental model became the key to the issue, and
having it earlier would have made my reproduction and implementation more
direct. Finally, I would plan the real PostgreSQL validation from the start
instead of first thinking about the problem mostly through configuration and
static code.

**What are you most proud of from this module?**
I am most proud that I took an area I had almost no experience with—database
migrations and CI—and followed it through as a complete workflow rather than
stopping when the script appeared to work. I reproduced a real schema mismatch,
fixed it without rewriting migration history, added an automatic check for
future pull requests, and tested the change against a fresh PostgreSQL database.
The most valuable result for me is not only PR #849; it is that I can now explain
the connection between application models, migration history, the real
database, tests, and CI, and I know how to verify each part instead of assuming
they agree.
