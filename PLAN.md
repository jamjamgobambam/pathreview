## Solution plan

**Issue:** Add a database migration validation step to CI that checks all migrations can be applied cleanly (https://github.com/ascherj/pathreview/issues/129)

### Understand
Right now the migrations only get checked by hand before a PR is merged. Nothing in CI confirms that all the Alembic migrations apply cleanly on a fresh database, or that the schema they build still matches the SQLAlchemy models. Since there is no automated check, drift has already gotten in. Migration `001_initial_schema.py` creates a unique constraint called `uq_users_email` on `users.email`, but the current `User` model doesn't declare that constraint anymore. It only sets `unique=True, index=True`, which makes a unique index instead. So the migrations build one extra thing the model doesn't know about.

The behavior I want: running the migrations from an empty database gives a schema that matches the models, and CI fails any PR where that isn't true. What actually happens: there is no CI check, and running `alembic check` locally already fails with a `remove_constraint uq_users_email` error (the reproduction is in JOURNAL.md).

### Map
Files I expect to change:
- `.github/workflows/ci.yml`, to add a new `validate-migrations` job.
- `scripts/validate_migrations.sh`, a new script that runs the two Alembic commands.
- To fix the existing drift, one of these two: `core/models/user.py` (add the `uq_users_email` constraint back to the model with `__table_args__`), or a new file in `alembic/versions/` (a migration that drops the redundant constraint).

Files I need to read but not change:
- `alembic/env.py`, to see how Alembic gets the database URL.
- `docker-compose.yml` and the existing `test-integration` job in `ci.yml`, since I'm copying their Postgres service container setup.

### Plan
1. Write `scripts/validate_migrations.sh` with `set -euo pipefail` so it runs `alembic upgrade head` and then `alembic check`.
2. Add a `validate-migrations` job to `ci.yml`. It starts a fresh Postgres service container (copied from `test-integration`), checks out the code, sets up Python, installs the deps, sets `DATABASE_URL`, and runs the script.
3. Fix the existing `uq_users_email` drift so `alembic check` passes. I still need to decide between updating the model or adding a drop-constraint migration.
4. Test it locally first. Bring up the stack, run the script by hand, and make sure both commands pass.
5. Push it and keep fixing the Actions run until it's green. Then add a fake drift on purpose to confirm the job goes red, and undo it.

### Inputs & outputs
Input: the repo's Alembic migrations and SQLAlchemy models, run against a fresh empty Postgres that the CI service container provides. Alembic reaches it through `DATABASE_URL`.

Output: a CI job that passes when the migrations apply cleanly and match the models, and fails (blocking the PR) when a migration is broken or drifted. It doesn't change any of the actual app code or how the app behaves.

### Risks & unknowns
- The existing `uq_users_email` drift means the check fails right away, so fixing it is part of this PR. I have to pick the fix without changing how email uniqueness actually works.
- I've never used GitHub Actions, so getting the service container, `DATABASE_URL`, and health check wired up will probably take a few tries. 
- I need to confirm the `alembic` in the script reads `DATABASE_URL` the same way the app does, through `alembic/env.py`.
- I already checked that `alembic check` exists in this project (Alembic 1.18.5), so I don't need a fallback.

### Edge cases
- A migration that applies fine but drifts from the models (what's happening now). The check has to catch it.
- A migration that's broken and won't apply. `upgrade head` has to fail, and `set -e` makes the whole job fail.
- A fresh database with nothing in it. The migrations have to run from the start, not assume the tables already exist.
- New migrations that other people add later. The job runs the whole chain up to `head`, not a fixed revision.
- Things autogenerate can miss, like some server defaults or check constraints. `alembic check` catches the common drift but not everything, which is worth knowing.

### Update (Week 9)

Step 3 decided: I updated the `User` model rather than adding a drop-constraint migration. The migration is what every existing database already has, so declaring the constraint in `__table_args__` matches reality without changing anyone's schema, and keeps this a CI-only PR.

One thing I didn't plan for: the repo has its own `alembic/` package directory, which shadows the installed `alembic` when the repo root is on `sys.path`. That doesn't affect the script or the CI job (the `alembic` CLI is fine), but it meant my unit tests had to read the migration files with `ast` instead of importing them.
