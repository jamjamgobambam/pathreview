# Issue #129 reproduction

## What I am reproducing

Issue #129 is a missing CI safeguard rather than a user-facing bug. PathReview has
an Alembic migration history, but the current GitHub Actions workflow never runs
that history or checks the resulting database schema against the SQLAlchemy
models. This means a pull request can pass the checks that currently exist
without proving that a database can be upgraded safely.

## Steps and observations

1. I inspected `.github/workflows/ci.yml`. It defines lint, typecheck, unit-test,
   integration-test, and frontend jobs. The integration job starts PostgreSQL,
   but it only runs `pytest tests/integration`; there is no `alembic upgrade
   head`, `alembic check`, or dedicated migration-validation job.
2. I ran `.venv/bin/alembic heads` and observed one current head: `002`.
3. I ran `.venv/bin/alembic history` and observed the ordered history
   `<base> -> 001 -> 002`.
4. I first ran `.venv/bin/alembic upgrade head --sql`. Alembic successfully
   generated 88 lines of PostgreSQL DDL for both revisions, confirming the
   intended migration path before I executed it.
5. I searched the CI workflow for `alembic` and `migration` and received no
   matches. Therefore, none of the current automatic checks exercises the
   migration path found in steps 2–4.
6. I installed PostgreSQL 16.14 locally and created a new empty database named
   `pathreview_migration_test`. With `DATABASE_URL` pointed at that database, I
   ran `.venv/bin/alembic upgrade head`. Revisions `001` and `002` both executed
   successfully, and `.venv/bin/alembic current` reported `002 (head)`.
7. I then ran `.venv/bin/alembic check` against the migrated database. It failed
   with `Detected removed unique constraint 'uq_users_email' on 'users'`,
   proving that the schema produced by the migrations does not currently match
   the SQLAlchemy metadata.
8. A read-only PostgreSQL query confirmed that `users.email` has both a
   `uq_users_email` unique constraint and a separate unique
   `ix_users_email` index. The model's `unique=True, index=True` describes the
   unique index, so the additional constraint is the pre-existing drift that
   the missing CI validation currently allows.

## Expected vs. actual

**Expected:** On every pull request, CI should create an isolated PostgreSQL
database, run every migration from base to head, and fail if the resulting
schema differs from the SQLAlchemy models.

**Actual:** CI can start PostgreSQL and run integration tests without ever
executing Alembic. A green build currently means the existing checks passed; it
does not mean the migration history is executable or free of schema drift.

## Reproduced result

The migration execution check passed, but the schema-consistency check failed
on a real, fresh PostgreSQL 16 database. This separates the two failure classes
the fix must cover: migrations may fail while executing, or they may execute
successfully and still produce the wrong final schema. The current CI runs
neither check, so it cannot report this real drift.
