## Solution plan

**Issue:** [Add a database migration validation step to CI that checks all migrations can be applied cleanly](https://github.com/ascherj/pathreview/issues/129)

### Understand

Schema migrations live under `alembic/versions/` and are only ever applied by
a developer running `make migrate` / `alembic upgrade head` locally — nothing
in `.github/workflows/ci.yml` does this. The `test-integration` job spins up
a Postgres service container but never points Alembic at it, and
`tests/integration/` currently has no test files, so
`pytest tests/integration -v --tb=short` collects 0 tests and exits 5
(confirmed locally, see reproduction commit). Expected behavior: CI applies
every migration to a fresh database in order and confirms the resulting
schema matches the SQLAlchemy models in `core/models/`, failing the build if
not. Actual behavior: nothing checks this, so a broken migration (or a
migration that drifts from the models) can merge to `main` silently.

This isn't hypothetical — running `alembic check` locally against a freshly
migrated database (see reproduction) already reports drift: migration `001`
creates an explicit `UniqueConstraint` named `uq_users_email` on
`users.email`, but `core/models/user.py:25` only declares
`unique=True, index=True` on the column, which SQLAlchemy represents as a
unique index, not a matching named constraint. So the "schema matches
models" half of this issue is currently false on `main`.

### Map

- `.github/workflows/ci.yml` — `test-integration` job (or a new dedicated
  `migrations` job) needs a step that runs the validation script against the
  existing `postgres` service.
- `scripts/validate_migrations.sh` — new script (named in the issue) that
  waits for Postgres, runs `alembic upgrade head`, then runs `alembic check`
  to assert no drift, and exits non-zero on either failure.
- `Makefile` — add a `migrate-check` target wrapping the same script, so the
  check has the same local/CI parity as `make check` does for lint/format/typecheck.
- `core/models/user.py` and/or a new `alembic/versions/003_*.py` — needed to
  resolve the pre-existing `uq_users_email` drift found above, otherwise the
  new CI check fails immediately on `main`.
- `docs/CONTRIBUTING.md` — mention the new `make migrate-check` step
  alongside the existing `make check` / `make test-unit` instructions.

### Plan

1. Write `scripts/validate_migrations.sh`: read `DATABASE_URL` from the
   environment (same convention as `alembic/env.py`), poll until Postgres is
   ready, run `alembic upgrade head`, then run `alembic check`, propagating
   a non-zero exit on any failure.
2. Add a `migrate-check` target to the `Makefile` that invokes the script
   locally against the dev `db` container, for parity with CI.
3. Add a step to the `test-integration` job in `ci.yml` (reusing its existing
   `postgres` service block) that installs deps and runs
   `scripts/validate_migrations.sh` before the pytest step.
4. Fix the existing `uq_users_email` drift — most likely by adding an
   explicit `UniqueConstraint("email", name="uq_users_email")` to
   `User.__table_args__` so the model matches migration `001` exactly (no
   new migration needed if the constraint already exists in the DB; only the
   model metadata is out of sync). Re-run `alembic check` locally to confirm
   the drift is gone.
5. Update `docs/CONTRIBUTING.md` to document `make migrate-check`, and verify
   the full flow end-to-end locally (`docker compose up -d db`, fresh
   volume, run the script) before opening the PR.

### Inputs & outputs

**Input:** `DATABASE_URL` pointing at a disposable Postgres instance (the
CI service container, or the local `docker compose` `db` service), the
migration chain in `alembic/versions/`, and the SQLAlchemy metadata in
`core/models/`.

**Output:** exit code `0` with a clear log line when migrations apply
cleanly and the resulting schema matches the models; non-zero exit with
Alembic's diff output (which migration failed, or which tables/columns/
constraints are out of sync) when either check fails — causing the CI job
to fail.

### Risks & unknowns

- The pre-existing `uq_users_email` drift means the new check fails on
  `main` from day one unless step 4 lands in the same PR — need to confirm
  whether fixing that drift belongs in this PR or should be split into a
  follow-up issue (leaning toward same PR, since otherwise the new CI gate
  would be broken immediately after merge).
- `alembic check` requires Alembic ≥1.9; `pyproject.toml` currently pins
  `alembic>=1.13.0`, which is fine, but worth double-checking the exact CI
  runner resolves a version that still supports the command.
- The CI Postgres service uses db `pathreview_test`; local dev uses
  `pathreview_dev` on port 5433. The script must read `DATABASE_URL` from
  the environment rather than hardcoding either, or `make migrate-check`
  will diverge from what CI actually runs.
- Running `make migrate-check` locally applies migrations to the real dev
  database (`pathreview_dev`), which is stateful — unlike CI's disposable
  service container. Need to decide whether to document this caveat or have
  the local target spin up an ephemeral throwaway DB instead.
- Unclear whether to add this as a new step in the existing
  `test-integration` job (simpler, reuses the service block) or a separate
  `migrations` job (cleaner failure signal, but duplicates the Postgres
  service config) — leaning toward reusing `test-integration` to avoid
  duplicating the service block, but open to feedback.

### Edge cases

- A migration that fails partway through (bad SQL, wrong column type) —
  the script must let Alembic's error surface and exit non-zero, not swallow
  it with `|| true` or similar.
- Schema drift that's intentional (e.g., a Postgres-specific feature Alembic
  can't autogenerate, like a partial index) — `alembic check` can false-positive
  here; the script's output needs to be clear enough that a developer can
  tell "real drift" from "known autogenerate limitation."
- A PR that adds a new migration file but doesn't update `core/models/` to
  match (or vice versa) — this is the exact case `alembic check` exists to
  catch, so it should be exercised as part of manual testing before merge.
- Fresh clone with zero migrations applied yet (`alembic current` returns
  nothing) — `alembic upgrade head` should still succeed from a blank
  database; already implicitly covered since that's what the reproduction
  step did.
