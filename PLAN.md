## Solution plan

**Issue:** Add a database migration validation step to CI that checks all migrations can be applied cleanly — https://github.com/ascherj/pathreview/issues/129

### Understand
Right now the database migrations are only checked by hand before a PR is merged. Nothing in CI verifies that (a) all Alembic migrations apply cleanly on a fresh database, and (b) the schema they build still matches the SQLAlchemy models. Because there is no automated check, drift has already slipped in: migration `001_initial_schema.py` creates a unique constraint `uq_users_email` on `users.email`, but the current `User` model no longer declares that constraint — it only sets `unique=True, index=True`, which produces a unique index. So the migrations build one extra thing the model does not know about.

- **Expected:** running the migrations from an empty database produces a schema that matches the models, and CI fails any PR where that is not true.
- **Actual:** there is no CI enforcement, and running `alembic check` locally already fails with `remove_constraint uq_users_email` (see the reproduction in JOURNAL.md).

### Map
Files I expect to touch:
- `.github/workflows/ci.yml` — add a new `validate-migrations` job.
- `scripts/validate_migrations.sh` — new script that runs the two Alembic commands.
- Resolve the existing drift in **one** of these:
  - `core/models/user.py` — add the `uq_users_email` constraint to the model via `__table_args__`, **or**
  - a new file in `alembic/versions/` — a migration that drops the redundant `uq_users_email` constraint.

Files I need to read but not edit:
- `alembic/env.py` — to confirm how Alembic reads the database URL.
- `docker-compose.yml` and the existing `test-integration` job in `ci.yml` — the Postgres service-container pattern I will copy.

### Plan
1. Write `scripts/validate_migrations.sh` with `set -euo pipefail` that runs `alembic upgrade head` then `alembic check`.
2. Add a `validate-migrations` job to `ci.yml`: a fresh Postgres service container (copied from `test-integration`), checkout, set up Python, install deps, set `DATABASE_URL`, and run the script.
3. Resolve the existing `uq_users_email` drift so `alembic check` passes (decide between updating the model or adding a drop-constraint migration).
4. Test locally — bring up the stack, run the script by hand, confirm `upgrade head` and `check` both pass.
5. Push and iterate on the GitHub Actions run until it is green; then deliberately introduce a fake drift to confirm the job goes red, and revert it.

### Inputs & outputs
- **Input:** the repo's Alembic migrations and SQLAlchemy models, run against a fresh, empty Postgres provided by the CI service container (reached via `DATABASE_URL`).
- **Output:** a CI job that exits `0` (green) when the migrations apply cleanly and match the models, and exits non-zero (red, blocking the PR) when a migration is broken or drifted. No production application code or runtime behavior changes.

### Risks & unknowns
- The existing `uq_users_email` drift means the check fails on day one, so resolving it is part of this PR — I need to pick the fix (model vs. new migration) without changing the actual email-uniqueness behavior.
- I am new to GitHub Actions, so wiring the service container, `DATABASE_URL`, and the health check may take a few push-and-watch iterations (a common failure is "connection refused" if the job runs before Postgres is ready).
- I need to confirm the script's `alembic` reads `DATABASE_URL` the same way the app does (through `alembic/env.py` / settings).
- `alembic check` is confirmed available (Alembic 1.18.5), so no fallback is needed.

### Edge cases
- A migration that applies fine but drifts from the models (the current case) — `check` must catch it.
- A migration that is broken and won't apply — `upgrade head` must fail and, via `set -e`, fail the whole job.
- A fresh database with no prior state — migrations must run from base, not assume existing tables.
- Future migrations added by other contributors — the job validates the full chain up to `head`, not a fixed revision.
- Autogenerate blind spots — `alembic check` catches common drift but not 100% (some server-side defaults / check constraints), which is a known limitation to note.
