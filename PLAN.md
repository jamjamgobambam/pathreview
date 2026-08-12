# Solution plan

**Issue:** [#129 — Add a database migration validation step to CI that checks all migrations can be applied cleanly](https://github.com/ascherj/pathreview/issues/129)

## Understand

PathReview represents its database in three related places: SQLAlchemy models
describe the schema the application expects now, Alembic revisions describe how
an older database reaches that schema, and PostgreSQL holds the schema that
actually exists. The current CI workflow tests several parts of the application
and even starts PostgreSQL for integration tests, but it never runs Alembic.
Therefore, CI does not prove either that revisions `001` and `002` can be
applied in order or that their final schema matches `core.models.Base.metadata`.

The expected behavior is that each pull request gets a fresh database and CI
turns red for either of two failure classes: a migration that cannot execute, or
a migration that executes but produces schema drift. The actual behavior is
that both cases can be outside the checks currently run by CI.

## Map

Files I expect to change:

- `.github/workflows/ci.yml`: add an isolated migration-validation job with a
  temporary PostgreSQL service and an async database URL.
- `scripts/validate_migrations.sh`: add the reusable, fail-fast entry point that
  runs the two Alembic validations.
- `alembic/versions/003_*.py`: only if the new consistency check reveals a real
  mismatch that must be corrected without rewriting an already-applied
  revision.

Files I need to understand and use, but do not currently expect to change:

- `alembic/env.py`: connects Alembic through an async SQLAlchemy engine and sets
  `target_metadata = Base.metadata`.
- `alembic/versions/001_initial_schema.py` and
  `alembic/versions/002_add_error_message_to_reviews.py`: the complete migration
  history that CI must exercise.
- `core/models/*.py`: the expected schema used by `alembic check`.
- `core/config.py`: loads `DATABASE_URL`; its async driver requirements must
  match the CI environment.

## Plan

1. Create `scripts/validate_migrations.sh`. Make it fail clearly when
   `DATABASE_URL` is absent, then run `alembic upgrade head` followed by
   `alembic check`. Preserve each command's non-zero exit status so GitHub
   Actions marks the job failed.
2. Add a separate migration job to `.github/workflows/ci.yml`. Reuse the
   repository's PostgreSQL 16 service pattern, install the project on Python
   3.11, and pass a `postgresql+asyncpg://` URL because `alembic/env.py` creates
   an async engine.
3. Run the validation against a disposable, empty PostgreSQL database. The
   local reproduction has already shown that revisions `001` and `002` execute
   successfully and that `alembic check` then fails on a real mismatch. Repeat
   the same experiment in GitHub Actions to prove the CI wiring is correct.
4. Correct the confirmed `users.email` drift. Migration `001` creates both
   `uq_users_email` and a unique `ix_users_email`, while the current model's
   `unique=True, index=True` describes the unique index. Add a new revision
   that removes the redundant constraint rather than editing the
   already-applied `001`, then confirm `alembic check` passes.
5. Run focused validation and review the CI diff for unrelated changes. Update
   `JOURNAL.md` with results, risks discovered, and links before opening the
   Week 9 pull request.

## Inputs & outputs

The validation takes:

- a `DATABASE_URL` that points to a fresh, disposable PostgreSQL database;
- the ordered files in `alembic/versions`;
- the SQLAlchemy metadata imported by `alembic/env.py`.

It produces no application data or UI change. Its primary output is a process
exit code: zero when all revisions apply and the final schema matches the
models, non-zero when migration execution or schema comparison fails. In
GitHub Actions, that exit code becomes a visible green or red pull-request
check, with Alembic's output explaining the failure.

## Risks & unknowns

- The current migration history already differs from the models:
  `alembic check` detected the extra `uq_users_email` unique constraint after
  revisions `001` and `002` were applied to fresh PostgreSQL 16. The correction
  must preserve the existing unique index and must not rewrite revision `001`.
- `alembic/env.py` uses `create_async_engine`; a plain `postgresql://` URL may
  select an incompatible synchronous driver. CI should use
  `postgresql+asyncpg://`.
- A reused or partially migrated database could produce misleading results.
  The CI job must receive a new isolated service database on every run.
- `alembic check` depends on all relevant model modules being registered in
  `Base.metadata`. An incomplete model import could create a false comparison.
- PostgreSQL may be started but not ready to accept connections. The service
  health check must gate the validation step.
- Existing unrelated CI failures must not be presented as failures introduced
  or fixed by this change.

## Edge cases

- A revision contains invalid SQL or refers to a missing table/column:
  `alembic upgrade head` should fail the job.
- A model changes without a matching revision: `alembic check` should fail the
  job after the existing revisions are applied.
- Two contributors create separate heads: validation should report the
  ambiguous history rather than silently choosing one branch.
- A revision references an unknown `down_revision`: the upgrade must fail with
  a useful Alembic error.
- `DATABASE_URL` is absent or points to the wrong driver: the script should exit
  early and explain the configuration problem.
- The database is already at head: validation should remain safe and
  repeatable, although CI will normally provide an empty database.

## Implementation results

- Added revision `003`, which removes only the redundant
  `uq_users_email` constraint. The existing unique `ix_users_email` index still
  enforces email uniqueness.
- Added `scripts/validate_migrations.sh` as the single local and CI entry point
  for `alembic upgrade head` and `alembic check`.
- Added an isolated `migrations` GitHub Actions job backed by PostgreSQL 16.
- Added four unit tests covering the revision chain, upgrade and downgrade
  operations, and the script's missing-configuration failure.
- Recreated the local validation database from scratch. Revisions `001`, `002`,
  and `003` applied successfully, and `alembic check` reported
  `No new upgrade operations detected`. Revision `003` was also downgraded and
  reapplied successfully.
- The focused test file passes (`4 passed`). The full unit suite has the same
  pre-existing failure baseline before and after this work: 52 failures and 31
  errors; the passing count increased from 345 to 349. Ruff still reports the
  same 182 pre-existing repository errors, while all changed Python files pass
  focused Ruff and Black checks.
